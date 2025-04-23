import hashlib
import hmac
import time

from django.conf import settings

from dchat_messages.models import DChatFile


def add_hmac(iterable: list[DChatFile] = None, single_object: DChatFile = None):
    """Adds a property named "hmac" to the provided Model objects"""

    _expiry_time = getattr(settings, "DCHAT_FILE_ACCESS_VALIDITY", 3600)
    secret_key = getattr(settings, "SECRET_KEY").encode("utf-8")
    expiry_time = int(time.time()) + _expiry_time

    # TODO
    # 1. check if single_object is and instance of model.Model

    if iterable:
        for element in iterable:
            if element:
                file_path = element.file.url
                access_token = element.token
                data = f"{file_path}_{access_token}_{expiry_time}".encode()
                hmac_obj = hmac.new(secret_key, data, hashlib.sha256)
                hex_digest = hmac_obj.hexdigest()
                element.hmac = hex_digest
                element.exp_time = expiry_time

    if single_object:
        if single_object:
            file_path = single_object.file.url
            access_token = single_object.token
            data = f"{file_path}_{access_token}_{expiry_time}".encode()
            hmac_obj = hmac.new(secret_key, data, hashlib.sha256)
            hex_digest = hmac_obj.hexdigest()
            single_object.hmac = hex_digest
            single_object.exp_time = expiry_time
