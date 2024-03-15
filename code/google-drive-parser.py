from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.discovery import build
import vk_api
import pprint
import os
import json
import traceback

pp = pprint.PrettyPrinter(indent=4)

# Настраиваем сервисный аккаунт для работы с диском
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = f'{os.path.dirname(__file__)}/totemic-audio-417208-79c05bdc087a.json'
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

# Функция для получения ссылок на документы в диске Google Drive
def get_google_docs_links(service):
    """
    Get the links to all the Google Docs in the user's Drive.
    """
    results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name, mimeType, webViewLink)").execute()
    while results:
        for file in results.get('files', []):
            yield (file['name'], file['webViewLink'])
        if results.get('nextPageToken'):
            results = service.files().list(pageToken=results['nextPageToken'], pageSize=10, fields="nextPageToken, files(id, name, mimeType, webViewLink)").execute()
        else:
            break
    return results

# Функция для получения короткой ссылки на документ Google Drive через vk.cc
def get_short_link(need_full_url):
    # Объект бота представляющий собой группу, от которой приходят сообщения
    vk_session = vk_api.VkApi(token="токен группы вк")
    res = vk_session.method('utils.getShortLink', {'url': need_full_url})
    return res['short_url'][8:]

all_links = sorted([(name, get_short_link(link)) for name, link in get_google_docs_links(service)])[4:]
disc_links = dict(all_links)

# Создаем файл gd-discips-links.json и записываем ссылки на диски в него.
try:
    with open(f'{os.path.dirname(__file__)}/gd-discips-links.json', 'w', encoding='utf-8') as f_gd:
        json.dump(disc_links, f_gd, ensure_ascii=False, indent=4)
    print("Файл «gd-discips-links.json» успешно создан!")
except Exception as e:
    print("В процессе создания файла «gd-discips-links.json» возникла следующая ошибка:")
    print(traceback.format_exc())
