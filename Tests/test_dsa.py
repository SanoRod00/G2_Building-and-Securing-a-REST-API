"""Focused tests for the SMS parser and transaction lookup functions."""

import unittest

from dsa.API.parse_sms import parse_sms_message
from dsa.API.search_compare import find_transaction_by_dict, find_transaction_linearly


class SmsParserTests(unittest.TestCase):
    def test_parses_received_message_fields(self):
        body = (
            "You have received 2000 RWF from Jane Smith (*********013) "
            "on your mobile money account. Financial Transaction Id: 76662021700."
        )

        transaction = parse_sms_message(body)

        self.assertEqual(transaction["transaction_id"], "76662021700")
        self.assertEqual(transaction["transaction_type"], "received")
        self.assertEqual(transaction["amount_rwf"], 2000)
        self.assertEqual(transaction["counterparty"], "Jane Smith")

    def test_keeps_unknown_message_as_unparsed(self):
        transaction = parse_sms_message("A message with no supported transaction pattern.")

        self.assertEqual(transaction["transaction_type"], "unparsed")
        self.assertIsNone(transaction["transaction_id"])
        self.assertIsNone(transaction["amount_rwf"])


class TransactionLookupTests(unittest.TestCase):
    def setUp(self):
        self.transactions = [
            {"transaction_id": "100", "transaction_type": "received"},
            {"transaction_id": "200", "transaction_type": "payment"},
        ]
        self.transactions_by_id = {
            transaction["transaction_id"]: transaction
            for transaction in self.transactions
        }

    def test_linear_and_dictionary_lookup_return_same_record(self):
        expected = self.transactions[1]

        self.assertEqual(find_transaction_linearly(self.transactions, "200"), expected)
        self.assertEqual(find_transaction_by_dict(self.transactions_by_id, "200"), expected)

    def test_both_lookup_methods_return_none_for_missing_id(self):
        self.assertIsNone(find_transaction_linearly(self.transactions, "999"))
        self.assertIsNone(find_transaction_by_dict(self.transactions_by_id, "999"))


if __name__ == "__main__":
    unittest.main()