from pathlib import Path

from django import forms

from .models import Complaint

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024
# First bytes of real JPEG / PNG files - stops a renamed script being accepted as a photo.
MAGIC_NUMBERS = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")
BAD_FILE = "This file type or size is not allowed. Use a JPG or PNG image of 5 MB or less."


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["category", "description", "photo"]
        help_texts = {"photo": "Optional. JPG or PNG, up to 5 MB."}

    def clean_photo(self):
        """File-upload safety: extension, size, declared type and real content checks (TC-Sec-09)."""
        photo = self.cleaned_data.get("photo")
        if not photo:
            return photo
        if Path(photo.name).suffix.lower() not in ALLOWED_EXTENSIONS or photo.size > MAX_PHOTO_BYTES:
            raise forms.ValidationError(BAD_FILE)
        content_type = getattr(photo, "content_type", None)
        head = photo.read(8)
        photo.seek(0)
        if (content_type and content_type not in ALLOWED_CONTENT_TYPES) or not head.startswith(MAGIC_NUMBERS):
            raise forms.ValidationError(BAD_FILE)
        return photo
