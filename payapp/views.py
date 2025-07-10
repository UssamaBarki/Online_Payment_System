from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from .models import PaymentRequest, Payment
from register.models import OnlineAccount
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from payapp.utils import fetch_exchange_rates
from decimal import Decimal
from django.contrib.auth import authenticate, login

# REST implementation starts here

EXCHANGE_RATES = {
    'USD': {'GBP': 0.75, 'EUR': 0.85},
    'GBP': {'USD': 1.33, 'EUR': 1.14},
    'EUR': {'USD': 1.18, 'GBP': 0.88},
}


@api_view(['GET'])
def currency_conversion(request, currency1, currency2, amount):
    """
    RESTful API for hardcoded currency conversion.
    Example: /conversion/USD/GBP/100/
    """
    try:
        amount = float(amount)

        if currency1 in EXCHANGE_RATES and currency2 in EXCHANGE_RATES[currency1]:
            conversion_rate = EXCHANGE_RATES[currency1][currency2]
            converted_amount = round(amount * conversion_rate, 2)
            return Response({'converted_amount': converted_amount, 'rate': conversion_rate})

        return Response({'error': 'Unsupported currency'}, status=400)

    except ValueError:
        return Response({'error': 'Invalid amount'}, status=400)

def convert_currency(request):
    """
    Converts an amount using the RESTful API-based conversion and returns
    base currency, target currency, amount, exchange rate, and converted amount.
    """
    base = request.GET.get('base', 'GBP')
    target = request.GET.get('target', 'USD')
    amount = request.GET.get('amount', 1)

    try:
        amount = float(amount)
        converted = fetch_exchange_rates(base, target, amount)

        if converted is not None:
            exchange_rate = round(converted / amount, 4) if amount != 0 else None
            return JsonResponse({
                "base_currency": base,
                "target_currency": target,
                "amount": amount,
                "exchange_rate": exchange_rate,
                "converted_amount": converted
            })

        return JsonResponse({"error": "Conversion failed"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# REST implementation ends here

def home(request):
    return render(request, 'home.html')


def admin_required(user):
    """
    Checks if the user is an admin (superuser).
    """
    return user.is_superuser

# --- User Views Starts Here ---
@login_required
def dashboard(request):
    """
    User-specific dashboard view.
    """
    if request.user.is_superuser:
        messages.error(request, "Unauthorized access to dashboard!")
        return redirect('admin_dashboard')

    user_account = OnlineAccount.objects.get(user=request.user)

    # Direct Payments
    sent_direct_payments = Payment.objects.filter(sender=request.user, origin=Payment.DIRECT_PAYMENT)
    received_direct_payments = Payment.objects.filter(recipient=request.user, origin=Payment.DIRECT_PAYMENT,read_status=False )

    # Payments from Requests
    sent_request_payments = Payment.objects.filter(sender=request.user, origin=Payment.PAYMENT_REQUEST)
    received_request_payments = Payment.objects.filter(recipient=request.user, origin=Payment.PAYMENT_REQUEST,read_status=False)
    pending_requests = PaymentRequest.objects.filter(requestee=request.user, status='pending', read_status=False)
    requested_payments = PaymentRequest.objects.filter(requester=request.user)

    # Calculate the counts for new entries

    received_direct_payments_unread_count = received_direct_payments.count()
    received_request_payments_unread_count = received_request_payments.count()
    pending_requests_unread_count = pending_requests.count()

    # Define currency symbols
    currency_symbols = {
        'GBP': '£',
        'USD': '$',
        'EUR': '€',
    }
    user_currency_symbol = currency_symbols.get(user_account.currency, '')

    context = {
        'balance': user_account.balance,
        'currency_symbol': user_currency_symbol,
        'currency': user_account.currency,
        'sent_direct_payments': sent_direct_payments,
        'received_direct_payments': received_direct_payments,
        'sent_request_payments': sent_request_payments,
        'received_request_payments': received_request_payments,
        'pending_requests': pending_requests,
        'requested_payments': requested_payments,
        'received_direct_payments_unread_count': received_direct_payments_unread_count,
        'received_request_payments_unread_count': received_request_payments_unread_count,
        'pending_requests_unread_count': pending_requests_unread_count,
    }
    return render(request, 'payapp/dashboard.html', context)


@login_required
@transaction.atomic
def direct_payment(request):
    """
    Handles direct payments by users.
    """
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email')
        try:
            # Convert amount from POST and ensure it's a Decimal
            amount = Decimal(request.POST.get('amount', '0'))
        except Exception as e:
            messages.error(request, "Invalid amount value.")
            return redirect('dashboard')

        sending_currency = request.POST.get('currency', 'GBP')

        try:
            # Fetch user accounts
            recipient = User.objects.get(email=recipient_email)
            sender_account = OnlineAccount.objects.get(user=request.user)
            recipient_account = OnlineAccount.objects.get(user=recipient)

            # Debug logs
            print(f"Sender's Currency: {sender_account.currency}")
            print(f"Sending Currency: {sending_currency}")
            print(f"Recipient's Currency: {recipient_account.currency}")

            # Initialize variables
            converted_amount = Decimal('0')
            amount_in_sender_currency = amount

            # CASE 1: Sender's account currency equals the sending currency
            if sender_account.currency == sending_currency:
                amount_in_sender_currency = amount  # No conversion required for deduction
                if recipient_account.currency == sending_currency:
                    converted_amount = amount  # No conversion required for recipient
                    print("Same-Currency Transaction: No conversion applied for recipient.")
                else:
                    # Convert from sending_currency to recipient's currency
                    conv_value = fetch_exchange_rates(sending_currency, recipient_account.currency, float(amount))
                    if conv_value is not None:
                        converted_amount = Decimal(str(conv_value))
                        print("Cross-Currency Transaction: Conversion applied for recipient.")
                    else:
                        converted_amount = amount
                        print("Fallback: Unable to fetch conversion rate for recipient's currency.")
            else:
                # CASE 2: Sender's account currency is different from sending currency.
                conv_value_sender = fetch_exchange_rates(sending_currency, sender_account.currency, float(amount))
                if conv_value_sender is not None:
                    amount_in_sender_currency = Decimal(str(conv_value_sender))
                else:
                    amount_in_sender_currency = amount

                # Convert for recipient credit: from sending_currency to recipient_account.currency.
                conv_value_recipient = fetch_exchange_rates(sending_currency, recipient_account.currency, float(amount))
                if conv_value_recipient is not None:
                    converted_amount = Decimal(str(conv_value_recipient))
                else:
                    converted_amount = amount  # Fallback
                print("Cross-Currency Transaction: Conversions applied for both sender and recipient.")

            # Debug print amounts
            print(f"Amount Deducted (in Sender's Currency {sender_account.currency}): {amount_in_sender_currency}")
            print(f"Amount Credited (in Recipient's Currency {recipient_account.currency}): {converted_amount}")

            # Check if sender has sufficient balance
            if sender_account.balance >= amount_in_sender_currency:
                # Deduct from sender's account
                sender_account.balance -= amount_in_sender_currency
                sender_account.save()

                # Credit the recipient's account
                recipient_account.balance += converted_amount
                recipient_account.save()

                # Log the transaction
                Payment.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    amount=converted_amount,
                    currency=recipient_account.currency,
                    original_amount=amount,
                    original_currency=sending_currency,
                    origin=Payment.DIRECT_PAYMENT
                )

                messages.success(
                    request,
                    f"Payment of {amount} {sending_currency} sent successfully! "
                    f"Deducted {amount_in_sender_currency} {sender_account.currency} from your account."
                )
            else:
                messages.error(request, "Insufficient balance!")
        except User.DoesNotExist:
            messages.error(request, "Recipient not found!")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            print(f"Error: {e}")

        return redirect('dashboard')

    return


@login_required
def create_payment_request(request):
    """
    Handles payment request creation by users.
    """
    if request.method == 'POST':
        requestee_email = request.POST.get('requestee_email')
        amount_input = request.POST.get('amount')
        currency = request.POST.get('currency', 'GBP')

        try:
            amount = Decimal(amount_input)
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount.")
            return redirect('create_payment_request')

        try:
            requestee = User.objects.get(email=requestee_email)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('create_payment_request')

        # Create PaymentRequest with selected currency
        PaymentRequest.objects.create(
            requester=request.user,
            requestee=requestee,
            amount=amount,
            currency=currency
        )
        messages.success(request, "Payment request sent!")
        return redirect('dashboard')
    else:
        return


@login_required
@transaction.atomic
def accept_payment_request(request, request_id):
    """
    Handles payment request acceptance by users.
    Performs currency conversion using the RESTful API as needed.
    """
    payment_request = get_object_or_404(PaymentRequest, id=request_id)

    if payment_request.requestee != request.user:
        messages.error(request, "You are not authorized to accept this payment request.")
        return redirect('dashboard')

    # The sender here is the user accepting the request.
    sender_account = OnlineAccount.objects.get(user=request.user)
    # The recipient is the one who created the payment request.
    recipient_account = OnlineAccount.objects.get(user=payment_request.requester)

    # Initialize conversion variables.
    # Amount to be deducted from sender and amount to be credited to recipient.
    amount_in_sender_currency = payment_request.amount
    converted_amount = payment_request.amount

    # Convert for sender's deduction if sender's account currency differs from the request currency.
    if sender_account.currency != payment_request.currency:
        conv_value_sender = fetch_exchange_rates(
            payment_request.currency, sender_account.currency, float(payment_request.amount)
        )
        if conv_value_sender is not None:
            amount_in_sender_currency = Decimal(str(conv_value_sender))
            print("Converted amount for sender's deduction applied.")
        else:
            print("Fallback: Using raw amount for sender's deduction.")
    else:
        print("Same-Currency Transaction: No conversion for sender.")

    # Convert for recipient's credit if recipient's account currency differs from the request currency.
    if recipient_account.currency != payment_request.currency:
        conv_value_recipient = fetch_exchange_rates(
            payment_request.currency, recipient_account.currency, float(payment_request.amount)
        )
        if conv_value_recipient is not None:
            converted_amount = Decimal(str(conv_value_recipient))
            print("Converted amount for recipient's credit applied.")
        else:
            print("Fallback: Using raw amount for recipient's credit.")
    else:
        print("Same-Currency Transaction: No conversion for recipient.")

    # Debug: Print deduction and credit details.
    print(f"Amount Deducted (Sender's Currency - {sender_account.currency}): {amount_in_sender_currency}")
    print(f"Amount Credited (Recipient's Currency - {recipient_account.currency}): {converted_amount}")

    # Check if the sender (requestee) has sufficient balance.
    if sender_account.balance >= amount_in_sender_currency:
        # Deduct from sender's account.
        sender_account.balance -= amount_in_sender_currency
        sender_account.save()

        # Credit the recipient's account.
        recipient_account.balance += converted_amount
        recipient_account.save()

        # Create a payment record.
        Payment.objects.create(
            sender=request.user,
            recipient=payment_request.requester,
            amount=converted_amount,
            currency=payment_request.currency,
            origin=Payment.PAYMENT_REQUEST
        )

        # Update the payment request status to accepted.
        payment_request.status = 'accepted'
        payment_request.save()

        messages.info(
            request,
            f"You have successfully accepted the payment request of {payment_request.amount} {payment_request.currency}."
        )
    else:
        messages.error(request, "You have insufficient balance to complete the payment.")

    return redirect('dashboard')


@login_required
def reject_payment_request(request, request_id):
    """
    Handles payment request rejection by users.
    """
    payment_request = get_object_or_404(PaymentRequest, id=request_id)

    if payment_request.requestee != request.user:
        messages.error(request, "You are not authorized to reject this payment request.")
        return redirect('dashboard')

    payment_request.status = 'rejected'
    payment_request.save()

    messages.info(request, f"You have rejected a payment request of £{payment_request.amount}.")

    return redirect('dashboard')


@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    """
    Admin-specific dashboard view.
    """
    all_accounts = OnlineAccount.objects.all()
    all_payments = Payment.objects.all()
    all_requests = PaymentRequest.objects.all()

    users_data = []
    for account in all_accounts:
        user_transactions = {
            'username': account.user.username,
            'email': account.user.email,
            'balance': account.balance,
            'sent_payments': Payment.objects.filter(sender=account.user),
            'received_payments': Payment.objects.filter(recipient=account.user),
        }
        users_data.append(user_transactions)

    context = {
        'users_data': users_data,
        'all_requests': all_requests,
    }
    return render(request, 'payapp/admin_dashboard.html', context)



@login_required
def mark_all_as_read(request):
    if request.user.is_superuser:
        messages.error(request, "Unauthorized access to mark notifications!")
        return redirect('admin_dashboard')

    Payment.objects.filter(recipient=request.user, read_status=False).update(read_status=True)
    PaymentRequest.objects.filter(requestee=request.user, read_status=False).update(read_status=True)

    return JsonResponse({'status': 'success'})

