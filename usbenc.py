import base64

import win32com.client
import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

'''
Особенности:
Утилита и файл с сохранённым хешом устройства находятся на флешке

Порядок работы утилиты:
1. Вставляем флешку
2. Инициируем её как флешку для шифрования
3. Шифруем файл (добавляя к расширению .usbenc) с помощью id флешки
   (дополнительно дописывая в начало зашифрованного файла хеш флешки)
4. Расшифровываем файл, проверяя КОРРЕКТНОСТЬ РАСШИРЕНИЯ
   и СООТВЕТСТВИЕ ХЕША флешки хешу используемого устройства
   
Что доделать:
1. Удаление файлов при их шифровании/дешифровании (+)
2. Перехват исключений не блокирующий работу программы (+)
3. .requirments файл чтобы не париться с зависимостями (+)
4. autorun флешки при запуске (не работает)
'''



class UsbEncryptor:
    EXTENSION = '.usbenc'

    def __init__(self) -> None:
        self.device_id = self._get_current_device_id()
        m = hashlib.sha256()
        m.update(self.device_id.encode())
        self.hash = m.digest()
        self.f = Fernet(self._generate_fernet_key(self.device_id))

    @staticmethod
    def _generate_fernet_key(password):
        password = password.encode()
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(password)
        return base64.urlsafe_b64encode(digest.finalize())

    # Считаем что id текущего устройства последний в списке, т.к. только что подключили
    @staticmethod
    def _get_current_device_id():
        wmi = win32com.client.GetObject("winmgmts:")
        current_device_id = None
        for usb in wmi.InstancesOf("Win32_USBHub"):
            current_device_id = usb.DeviceID
        return current_device_id

    def encrypt(self, path):
        if self.EXTENSION in path:
            raise Exception('This file already encrypted or just have incorrect filename')

        with open(path, "rb") as file:
            # read all file data
            file_data = file.read()
        encrypted_data = self.f.encrypt(file_data)
        # Дописываем хеш устройства в начало файла
        with open(path + self.EXTENSION, "wb") as file:
            file.write(self.hash + encrypted_data)
        os.remove(path)

    def decrypt(self, path):
        if self.EXTENSION not in path:
            raise Exception('This file wasn''t encrypted or just have incorrect filename'
                            ' (doesn''t have extension .usbenc)')
        with open(path, "rb") as file:
            # read all file data
            file_data = file.read()

        if self.hash != file_data[:32]:
            raise Exception('This file was encrypted by another device!')

        decrypted_data = self.f.decrypt(file_data[32:])
        with open(path[: -len(self.EXTENSION)], "wb") as file:
            file.write(decrypted_data)
        os.remove(path)


if __name__ == '__main__':
    usbenc = UsbEncryptor()

    MENU = '1: encrypt file, 2: decrypt file'
    command = "0"
    while command != 0:
        print(MENU)
        command = input()
        try:
            if command == '1':
                usbenc.encrypt(input('Please, enter full path for file for encrypt: '))
                print('Encryption success')
            elif command == '2':
                usbenc.decrypt(input('Please, enter full path for file for decrypt: '))
                print('Decryption success')
            elif command == '0':
                break
            else:
                print("Unexpected command, please try again")
        except Exception as ex:
            print(ex)
