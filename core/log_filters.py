"""Logging helpers for data protection (HMS-NF-003, SAD 4.4 "What is never logged").

MaskPIIFilter masks email addresses and phone numbers in every log line, e.g.
"stu1@pes.edu" -> "s***@pes.edu" and "9876543210" -> "******3210".
"""
import logging
import re

EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?(\d{6})(\d{4})(?!\d)")


def mask_pii(text):
    text = EMAIL_RE.sub(r"\1***@\2", text)
    return PHONE_RE.sub(lambda m: "*" * 6 + m.group(2), text)


class MaskPIIFilter(logging.Filter):
    def filter(self, record):
        record.msg = mask_pii(record.getMessage())
        record.args = ()
        return True
