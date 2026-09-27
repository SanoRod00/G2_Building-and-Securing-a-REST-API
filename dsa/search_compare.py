"""Compare looking up MoMo transactions by scanning a list or using a dictionary."""

import json
import os
import time


# Load the parsed transaction dictionaries from the JSON file.
def load_transactions(json_path):
    with open(json_path, "r", encoding="utf-8") as input_file:
        return json.load(input_file)


# Check each transaction in order and return the one with the requested ID.
def find_transaction_linearly(transactions, transaction_id):
    for transaction in transactions:
        if transaction["transaction_id"] == transaction_id:
            return transaction
    return None


# Return the transaction stored under the requested ID in the dictionary.
def find_transaction_by_dict(transactions_by_id, transaction_id):
    return transactions_by_id.get(transaction_id)


# Pick unique IDs in turns across transaction types so one type does not dominate the sample.
def select_sample_ids(transactions, sample_size):
    ids_by_type = {}

    for transaction in transactions:
        transaction_id = transaction["transaction_id"]
        transaction_type = transaction["transaction_type"]

        if transaction_id is None:
            continue
        if transaction_type == "unparsed":
            continue

        if transaction_type not in ids_by_type:
            ids_by_type[transaction_type] = []
        if transaction_id not in ids_by_type[transaction_type]:
            ids_by_type[transaction_type].append(transaction_id)

    sample_ids = []
    type_names = list(ids_by_type.keys())
    position = 0

    while len(sample_ids) < sample_size:
        added_id = False

        for transaction_type in type_names:
            ids_for_type = ids_by_type[transaction_type]
            if position < len(ids_for_type):
                sample_ids.append(ids_for_type[position])
                added_id = True
                if len(sample_ids) == sample_size:
                    break

        if not added_id:
            break
        position += 1

    return sample_ids


# Time both search functions for every sampled ID and print their average times.
def time_search_methods(transactions, transactions_by_id, transaction_ids):
    repeat_count = 100
    print("Transaction ID | Linear search (seconds) | Dictionary lookup (seconds)")

    for transaction_id in transaction_ids:
        start_time = time.time()
        for repeat in range(repeat_count):
            find_transaction_linearly(transactions, transaction_id)
        linear_time = (time.time() - start_time) / repeat_count

        start_time = time.time()
        for repeat in range(repeat_count):
            find_transaction_by_dict(transactions_by_id, transaction_id)
        dictionary_time = (time.time() - start_time) / repeat_count

        print(
            f"{transaction_id} | {linear_time:.9f} | "
            f"{dictionary_time:.9f}"
        )


# Load the data, prepare both search methods, and compare at least 20 IDs when available.
def main():
    script_folder = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_folder, "output.json")
    transactions = load_transactions(json_path)

    transactions_by_id = {}
    for transaction in transactions:
        transaction_id = transaction["transaction_id"]
        if transaction_id is not None:
            if transaction_id not in transactions_by_id:
                transactions_by_id[transaction_id] = transaction

    sample_ids = select_sample_ids(transactions, 20)
    if len(sample_ids) < 20:
        print(f"Only {len(sample_ids)} unique transaction IDs are available.")
    time_search_methods(transactions, transactions_by_id, sample_ids)


if __name__ == "__main__":
    main()


# Reflection for the group report:
# A list search starts at the beginning and checks each transaction until it finds
# the ID, so IDs near the end take more checks than IDs near the beginning. A
# dictionary keeps each transaction under its ID, letting Python go directly to
# the matching entry instead of checking all the earlier transactions. That is
# why dictionary lookup is usually faster, especially as the list gets longer.
# In our test, linear search took approximately 45.088 microseconds on average to
# find a transaction, while dictionary lookup took approximately 0.17235
# microseconds, confirming the expected difference.
# Another option for a much larger dataset is a database table with an index on
# transaction ID; the index helps the database jump to matching records without
# loading and scanning every message, and it can keep the data stored on disk.
# One-time-password messages are excluded because they are not transactions, and
# five failed transaction attempts plus two reversals remain unparsed as edge cases.
