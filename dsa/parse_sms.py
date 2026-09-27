"""Read MoMo SMS messages and save the useful transaction details as JSON."""

import json
import os
import xml.etree.ElementTree as ElementTree


# Read the SMS elements from the XML so each message can be parsed separately.
def load_sms_messages(xml_path):
    tree = ElementTree.parse(xml_path)
    root = tree.getroot()
    return root.findall(".//sms")


# Find an explicitly labeled transaction ID, leaving it empty when the message has none.
def extract_transaction_id(body):
    marker = "Financial Transaction Id:"

    if marker in body:
        id_text = body.split(marker, 1)[1].strip()
    elif "TxId:" in body:
        id_text = body.split("TxId:", 1)[1].strip()
    else:
        return None

    id_parts = id_text.split("*", 1)[0].split()
    if not id_parts:
        return None

    transaction_id = id_parts[0].strip(".*,:;")
    if transaction_id.isdigit():
        return transaction_id
    return None


# Read the amount next to the wording used by each supported transaction type.
def extract_amount(body, transaction_type):
    if transaction_type == "received":
        amount_text = body.split("You have received ", 1)[1]
    elif transaction_type == "payment":
        amount_text = body.split("payment of ", 1)[1]
    elif transaction_type == "bank_deposit":
        if "bank deposit of " in body:
            amount_text = body.split("bank deposit of ", 1)[1]
        else:
            amount_text = body.split("DEPOSIT RWF ", 1)[1]
            amount_text = amount_text.split(" Receiver:", 1)[0]
    elif transaction_type == "transfer":
        if body.startswith("You have transferred "):
            amount_text = body.split("You have transferred ", 1)[1]
        else:
            amount_text = body.split("*165*S*", 1)[1]
    elif transaction_type == "bundle_purchase":
        amount_text = body.rsplit(" RWF", 1)[0].rsplit(" ", 1)[-1]
    elif transaction_type == "withdrawal":
        amount_text = body.split("withdrawn ", 1)[1]
    elif transaction_type == "direct_payment":
        amount_text = body.split("transaction of ", 1)[1]
    else:
        return None

    amount_text = amount_text.split(" RWF", 1)[0].strip()
    amount_text = amount_text.replace(",", "")

    if amount_text.isdigit():
        return int(amount_text)
    return None


# Find the named person or business involved when the SMS states one.
def extract_counterparty(body, transaction_type):
    if transaction_type == "received":
        name_text = body.split(" from ", 1)[1]
        counterparty = name_text.split(" (", 1)[0]
    elif transaction_type == "payment":
        name_text = body.split(" to ", 1)[1]
        name_text = name_text.split(" has been completed", 1)[0].strip()
        if " (" in name_text:
            counterparty = name_text.split(" (", 1)[0]
        else:
            name_parts = name_text.rsplit(" ", 1)
            if len(name_parts) == 2 and name_parts[1].isdigit():
                counterparty = name_parts[0]
            else:
                counterparty = name_text
    elif transaction_type == "transfer":
        if body.startswith("You have transferred "):
            name_text = body.split(" to ", 1)[1]
        else:
            name_text = body.split(" transferred to ", 1)[1]
        counterparty = name_text.split(" (", 1)[0]
    elif transaction_type == "bank_deposit" and "Receiver: " in body:
        counterparty = body.split("Receiver: ", 1)[1].split(" ", 1)[0]
    elif transaction_type == "withdrawal" and "via agent: " in body:
        name_text = body.split("via agent: ", 1)[1]
        counterparty = name_text.split(" (", 1)[0]
    elif transaction_type == "direct_payment":
        name_text = body.split(" by ", 1)[1]
        counterparty = name_text.split(" on your MOMO account", 1)[0].strip()
    else:
        return None

    return counterparty.strip() or None


# Turn one free-text SMS into a small dictionary that the API can use.
def parse_sms_message(body):
    if body.startswith("<#> Dear Customer, your MTN MoMo application one-time password is"):
        transaction_type = "authentication_code"
    elif body.startswith("You have received "):
        transaction_type = "received"
    elif (
        body.startswith("TxId:")
        or body.startswith("*162*TxId:")
        or body.startswith("Your payment of ")
    ):
        transaction_type = "payment"
    elif (
        body.startswith("*113*R*A bank deposit of ")
        or " DEPOSIT RWF " in body
    ):
        transaction_type = "bank_deposit"
    elif (
        body.startswith("*165*S*") and " transferred to " in body
    ) or body.startswith("You have transferred "):
        transaction_type = "transfer"
    elif " withdrawn " in body and " from your mobile money account" in body:
        transaction_type = "withdrawal"
    elif body.startswith("*164*S*") and "A transaction of " in body:
        transaction_type = "direct_payment"
    elif body.startswith("Yello!"):
        transaction_type = "bundle_purchase"
    else:
        transaction_type = "unparsed"

    transaction = {
        "transaction_id": extract_transaction_id(body),
        "transaction_type": transaction_type,
        "amount_rwf": extract_amount(body, transaction_type),
        "counterparty": extract_counterparty(body, transaction_type),
        "body": body,
    }
    return transaction


# Parse every SMS and show how many messages matched a known transaction pattern.
def parse_sms_file(xml_path):
    sms_messages = load_sms_messages(xml_path)
    transactions = []

    for sms_message in sms_messages:
        body = sms_message.attrib.get("body", "")
        transactions.append(parse_sms_message(body))

    unparsed_count = 0
    authentication_code_count = 0
    for transaction in transactions:
        if transaction["transaction_type"] == "unparsed":
            unparsed_count += 1
        elif transaction["transaction_type"] == "authentication_code":
            authentication_code_count += 1

    total_transaction_count = len(transactions) - authentication_code_count
    parsed_count = total_transaction_count - unparsed_count
    print(
        f"{parsed_count} of {total_transaction_count} transactions parsed "
        f"successfully, {unparsed_count} unparsed. "
        f"Excluded {authentication_code_count} authentication code messages "
        f"from transaction totals ({len(transactions)} SMS messages overall)."
    )
    return transactions


# Save the parsed transactions in a JSON file that teammates can load later.
def save_transactions(transactions, output_path):
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(transactions, output_file, indent=2, ensure_ascii=False)


# Use paths beside this script so it works when started from any folder.
def main():
    script_folder = os.path.dirname(os.path.abspath(__file__))
    project_folder = os.path.dirname(script_folder)
    xml_path = os.path.join(project_folder, "modified_sms_v2-1.xml")
    output_path = os.path.join(script_folder, "output.json")

    transactions = parse_sms_file(xml_path)
    save_transactions(transactions, output_path)


if __name__ == "__main__":
    main()
