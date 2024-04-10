from flask import Flask, request, json
from faq import FAQ
import vk_api
import telebot
import traceback
import os
from telebot import types
from vk_api.utils import get_random_id
import json as JSON
import time

# Объект бота представляющий собой группу, от которой приходят сообщения
vk_session = vk_api.VkApi(token="токен вк группы")

app = Flask(__name__)


def send_message(peer_id, message, keyboard=None, attachment=None):
    args = {
        'peer_id': peer_id,
        'message': message,
        'random_id': get_random_id()
    }
    if keyboard is not None:
        args['keyboard'] = JSON.JSONEncoder().encode(keyboard)
    elif attachment is not None:
        args['attachment'] = attachment
    vk_session.method('messages.send', args)


main_kb_faq = {
    "one_time": False,
    "inline": False,
    "buttons": [
        [
            {
                "action": {
                    "type": "text",
                    "payload": {
                        "function": "update"
                    },
                    "label": "💫 Обновить таблицу"
                },
                "color": "primary"
            }
        ],
        [
            {
                "action": {
                    "type": "text",
                    "payload": {
                        "function": "help"
                    },
                    "label": "❓ Помощь"
                },
                "color": "secondary"
            }
        ]
    ]
}

plug_kb = {
    "inline": True,
    "buttons": [
        [
            {
                "action": {
                    "type": "text",
                    "payload": {
                        "function": "plug_on"
                    },
                    "label": "Включить"
                },
                "color": "positive"
            },
            {
                "action": {
                    "type": "text",
                    "payload": {
                        "function": "plug_off"
                    },
                    "label": "Выключить"
                },
                "color": "negative"
            }
        ]
    ]
}

chat_kb = {
    "inline": True,
    "buttons": [
        [
            {
                "action": {
                    "type": "text",
                    "payload": {
                        "function": "chat_on"
                    },
                    "label": "Включить"
                },
                "color": "positive"
            }
        ],
        [
            {
                "action": {
                    "type": "text",
                    "payload": {
                        "function": "chat_off"
                    },
                    "label": "Выключить"
                },
                "color": "negative"
            }
        ]
    ]
}

# айди беседы тестовой для работы с ботом (id чата администраторов)
id_testchat = "2000000001"
id_admin_chat = "368424892"

faq_table = FAQ(name="FAQ система",
                sheet_link="https://docs.google.com/spreadsheets/d/1iYKz7fNpviX2r15v7QNlcYbYan2MGYqonytu05RDh6c/edit#gid=0")

# Логический флаг для функционирования механики обращения пользователей в поддержку
is_problem = False

# Логический флаг для функционирования работы режима заглушки у бота
is_plug = False

# Логический флаг для функционирования работы состояния чат-бота у системы
is_chat = False
chat_counter = 1


@app.route('/', methods=["POST"])  # функция, принимающая запросы
def main():
    global is_problem, is_plug, is_chat, chat_counter
    try:
        # Преобразовываем json-ответ в питоновский объект
        data = json.loads(request.data)
        templates = faq_table.get_templates()  # Получение актуальной клавиатуры кнопок

        try:  # Защита от повторных действий с помощью логов
            with open(f'{os.path.dirname(__file__)}/log.json', 'r', encoding="utf-8") as read_file:
                log = json.load(read_file)
        except FileNotFoundError:
            log = []

        if data['event_id'] in log:  # если уже было, то выходим
            return "ok"
        else:
            log.append(data['event_id'])
            with open(f'{os.path.dirname(__file__)}/log.json', 'w') as write_file:
                json.dump(log, write_file)

        if data["type"] == "confirmation":  # Если событие — подтверждение группы
            return "cfae6f7d"

        if data["type"] == "message_new":  # Если событие — сообщение
            object_0 = data["object"]["message"]
            object_1 = data["object"]["client_info"]

            peer_id = object_0["peer_id"]
            body = object_0["text"]
            from_id = str(object_0["from_id"])
            attachments = object_0["attachments"]

            keyboard_work = object_1["keyboard"]

            if keyboard_work == 1:

                # функционал бота, который работает везде

                # функция, показывающая id беседы (чата или переписки с пользователем)
                if body.lower()[:5] == "!айди":
                    send_message(peer_id, message=peer_id)
                    return "ok"

                elif body.lower()[:7] == "!начать":
                    template = templates['menu']
                    send_message(peer_id, **template)
                    return "ok"

                # функционал бота, который работает в чате администраторов
                if str(peer_id) == id_testchat:
                    if body.lower()[:7] == "!помощь":
                        msg = "Добро пожаловать в чат администраторов Дипломного проекта!\n\nКоманды, доступные в этом чате:\n\n1) !старт — позволяет вывести кнопки для обновления данных таблицы и вывода информации о таблице и группе проекта.\n\n2) !заглушка — помогает ввести в бота заглушку на возможные ошибки в работе и выводить сообщение о ведении технических работ над ботом группы!\n\nПриятного пользования!!!"
                        send_message(peer_id, msg)

                    elif body.lower()[:6] == "!старт":
                        send_message(
                            peer_id, f"{faq_table.__str__()}\n\nЧем могу помочь?", main_kb_faq)

                    # функция заглушки работы бота
                    elif body.lower()[:9] == "!заглушка":
                        send_message(
                            peer_id, "Функция заглушки работы бота. Что стоит сделать с ней?", plug_kb)

                # функционал бота, который работает в личке
                else:

                    # Также при включённом режиме заглушки отправляем пользователю сообщение о ведении технических работ
                    if is_plug:
                        send_message(
                            peer_id, "Сейчас ведутся технические работы, попробуй повторить попытку позже")
                        return "ok"
                    else:

                        # если пользователь отправляет стикер, то получает его же в ответ (принцип эхо-сервера)
                        try:
                            if len(object_0["attachments"]) != 0:
                                if object_0["attachments"][0]["type"] == "sticker":
                                    args = {
                                        'peer_id': peer_id,
                                        'sticker_id': object_0["attachments"][0]["sticker"]["sticker_id"],
                                        'random_id': get_random_id()
                                    }
                                    vk_session.method('messages.send', args)
                                return 'ok'
                        except Exception as e:
                            pass

                        if is_problem:
                            # 2. получение текста с проблемой-вопросом от пользователя и его передача в чат администраторов
                            user_name = vk_session.method(
                                "users.get", {"user_ids": peer_id, "name_case": "Nom"})
                            notification = "@id" + from_id + " (" + user_name[0]['first_name'] + " " + user_name[0][
                                'last_name'] + ") написал(-а) в группу сообщение:\n\n<<" + body + ">>\n\nЧеловек ждёт ответа: vk.com/gim161181001?sel=" + from_id + "\nСсылка на сообщения группы: vk.com/gim161181001"
                            send_message(id_testchat, message=notification)

                            # 3. отправка пользователю сообщения о том, что информация о проблеме-вопросе успешно принята!
                            done_msg = 'Отлично! Информацию приняли, тебе в скором времени придёт ответ!'
                            send_message(peer_id, message=done_msg)

                            is_problem = False
                            time.sleep(1)

                            # 4. автоматический вывод главного шаблона после отправки сообщения с проблемой
                            template = templates['menu']
                            send_message(peer_id, **template)

                        if is_chat:
                            # начало работы чат-бота с NLP (функционирование user says)

                            # отображение функции "бот печатает..."
                            arguments = {
                                "peer_id": peer_id,
                                "type": "typing"
                            }
                            vk_session.method(
                                'messages.setActivity', arguments)

                            time.sleep(1)

                            search_user_says = faq_table.search_user_says(
                                body.lower())
                            faq_table.clean_template_scores()
                            faq_table.clean_napr_sphere_scores()

                            # случай, когда юзер сейсы не дали вообще никакого результата — сигнал об ошибке в программе
                            # тут с целью поддержания диалога с пользователем в ответ выдаётся то же сообщение, которое пользователь ввёл
                            # и на которое бот не нашёл вообще никакого шаблона в базе

                            if "payload" not in object_0.keys():
                                # подготовка клавиатуры для обработки ситуаций с неточными и точными совпадениями (топ-5)

                                # список заголовков для inline-кнопок
                                labels_templates = faq_table.render_full_names_templates()

                                keyboard = {
                                    "inline": True,
                                    "buttons": []
                                }

                                if type(search_user_says[0]) == str:
                                    # ловим кейсы с выводом аналитической сводки по всем РПД
                                    # относительно введённого пользователем ключевого слова

                                    msg_output = search_user_says[0]
                                    potential_templates = search_user_says[1][1:]

                                    if search_user_says[1][0] == 5:
                                        button = [
                                            [
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[0]
                                                        },
                                                        "label": labels_templates[potential_templates[0]]
                                                    },
                                                    "color": "primary"
                                                },
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[1]
                                                        },
                                                        "label": labels_templates[potential_templates[1]]
                                                    },
                                                    "color": "primary"
                                                }
                                            ],
                                            [
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[2]
                                                        },
                                                        "label": labels_templates[potential_templates[2]]
                                                    },
                                                    "color": "primary"
                                                },
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[3]
                                                        },
                                                        "label": labels_templates[potential_templates[3]]
                                                    },
                                                    "color": "primary"
                                                }
                                            ],
                                            [
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[4]
                                                        },
                                                        "label": labels_templates[potential_templates[4]]
                                                    },
                                                    "color": "primary"
                                                }
                                            ]
                                        ]

                                    elif search_user_says[1][0] == 3:
                                        button = [
                                            [
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[0]
                                                        },
                                                        "label": labels_templates[potential_templates[0]]
                                                    },
                                                    "color": "primary"
                                                },
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[1]
                                                        },
                                                        "label": labels_templates[potential_templates[1]]
                                                    },
                                                    "color": "primary"
                                                }
                                            ],
                                            [
                                                {
                                                    "action": {
                                                        "type": "text",
                                                        "payload": {
                                                            "template": potential_templates[2]
                                                        },
                                                        "label": labels_templates[potential_templates[2]]
                                                    },
                                                    "color": "primary"
                                                }
                                            ]
                                        ]

                                    button5 = str(button).replace("'", '"')
                                    button55 = json.loads(button5)
                                    keyboard["buttons"] = button55

                                    send_message(
                                        peer_id, message=msg_output, keyboard=keyboard)
                                    return "ok"

                                # очень много есть случаев и кейсов обработки юс, которые я сгруппировал по индикаторам ниже

                                # список наших потенциальных templates
                                potential_templates = search_user_says[1:]

                                # точное попадание под юс и template
                                if search_user_says[0] == 0:
                                    name_template = search_user_says[1]
                                    if name_template == "support_0":
                                        # тут будет функционал по отправке вопроса в чат администраторов

                                        # 1. отправка пользователю сообщения о том, что он может описать свою проблему поподробнее ниже
                                        template = templates['support_0']
                                        send_message(peer_id, **template)
                                    else:
                                        template = templates[name_template]
                                        send_message(peer_id, **template)

                                # ситуация, когда найдено 2 точных совпадения
                                elif search_user_says[0] == 2:
                                    button = [
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[0]
                                                    },
                                                    "label": labels_templates[potential_templates[0]]
                                                },
                                                "color": "primary"
                                            }
                                        ],
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[1]
                                                    },
                                                    "label": labels_templates[potential_templates[1]]
                                                },
                                                "color": "primary"
                                            }
                                        ]
                                    ]

                                    button2 = str(button).replace("'", '"')
                                    button22 = json.loads(button2)
                                    keyboard["buttons"] = button22

                                    message = "Наверное, ты имел(-а) в виду"
                                    send_message(
                                        peer_id, message=message, keyboard=keyboard)

                                # ситуация, когда найдено 3 точных совпадения
                                elif search_user_says[0] == 3:
                                    button = [
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[0]
                                                    },
                                                    "label": labels_templates[potential_templates[0]]
                                                },
                                                "color": "primary"
                                            },
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[1]
                                                    },
                                                    "label": labels_templates[potential_templates[1]]
                                                },
                                                "color": "primary"
                                            }
                                        ],
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[2]
                                                    },
                                                    "label": labels_templates[potential_templates[2]]
                                                },
                                                "color": "primary"
                                            }
                                        ]
                                    ]

                                    button3 = str(button).replace("'", '"')
                                    button33 = json.loads(button3)
                                    keyboard["buttons"] = button33

                                    message = "Наверное, ты имел(-а) в виду"
                                    send_message(
                                        peer_id, message=message, keyboard=keyboard)

                                elif len(potential_templates) == 5:
                                    button = [
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[0]
                                                    },
                                                    "label": labels_templates[potential_templates[0]]
                                                },
                                                "color": "primary"
                                            },
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[1]
                                                    },
                                                    "label": labels_templates[potential_templates[1]]
                                                },
                                                "color": "primary"
                                            }
                                        ],
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[2]
                                                    },
                                                    "label": labels_templates[potential_templates[2]]
                                                },
                                                "color": "primary"
                                            },
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[3]
                                                    },
                                                    "label": labels_templates[potential_templates[3]]
                                                },
                                                "color": "primary"
                                            }
                                        ],
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": potential_templates[4]
                                                    },
                                                    "label": labels_templates[potential_templates[4]]
                                                },
                                                "color": "primary"
                                            }
                                        ]
                                    ]

                                    button5 = str(button).replace("'", '"')
                                    button55 = json.loads(button5)
                                    keyboard["buttons"] = button55

                                    # ситуация, когда найдено 5 и более точных совпадений
                                    if search_user_says[0] == 5:
                                        message = "Наверное, ты имел(-а) в виду"
                                        send_message(
                                            peer_id, message=message, keyboard=keyboard)

                                    # вывод 5 примерных template под текст пользователя (0 точных совпадений)
                                    elif search_user_says[0] == -1:
                                        message = "Возможно, ты имел(-а) в виду"
                                        send_message(
                                            peer_id, message=message, keyboard=keyboard)

                            # реагирование на ситуации, когда пользователь не печатает текст, а пользуется кнопками
                            else:
                                # здесь мы ловим ситуацию и запоминаем её при прослушивании текста с проблемой-вопросом
                                is_problem = False
                        else:

                            # чекаем, идёт ли пользователь по кнопкам или просто печатает текст
                            if "payload" not in object_0.keys():
                                # если пользователь просто вкидывает текст боту, то
                                # на каждое 5 сообщение ему будет прилетать напоминание о включении режима чат-бота

                                kb_faq = {
                                    "inline": True,
                                    "buttons": [
                                        [
                                            {
                                                "action": {
                                                    "type": "text",
                                                    "payload": {
                                                        "template": "menu"
                                                    },
                                                    "label": "Главное меню"
                                                },
                                                "color": "primary"
                                            }
                                        ]
                                    ]
                                }

                                if chat_counter == 5:
                                    # отображение функции "бот печатает..."
                                    arguments = {
                                        "peer_id": peer_id,
                                        "type": "typing"
                                    }
                                    vk_session.method(
                                        'messages.setActivity', arguments)

                                    time.sleep(1)
                                    send_message(peer_id, message="Если хочешь пообщаться с ботом, то перейди в главное меню и выбери кнопку «Чат-бот».\nВ таком случае откроется доступ на общение с ботом на учебные и не только темы.\n\nЕсли у тебя появились вопросы касательно системы и не только, то можешь обратиться в раздел поддержки в главном меню по кнопке «Поддержка».\n\nТак ты сможешь оперативно связаться с администратором/разработчиком системы и отправить свой вопрос!", keyboard=kb_faq)
                                    chat_counter = 1
                                else:
                                    chat_counter += 1
                            else:
                                # здесь мы ловим ситуацию и запоминаем её при прослушивании текста с проблемой-вопросом
                                is_problem = False

                try:
                    payload = JSON.JSONDecoder().decode(object_0["payload"])
                    if payload["function"] == "update":

                        # ловим ошибку при выполнении обновления таблицы
                        try:
                            templates = faq_table.render_templates()
                            send_message(peer_id, "Данные обновлены!!!")
                            is_update = False
                        except JSON.decoder.JSONDecodeError:
                            send_message(
                                peer_id, "При обновлении данных таблицы возникла ошибка!\nВ скором времени администратор решит данную проблему.")
                            message = "Возникла ошибка в системе, пора фиксить :)\n\n" + \
                                str(traceback.format_exc())
                            send_message(peer_id='368424892', message=message)

                    if payload["function"] == "help":
                        send_message(
                            peer_id, f"{faq_table.__str__()}", main_kb_faq)

                    if payload["function"] == "plug_on":
                        is_plug = True
                        send_message(peer_id, "Заглушка успешно включена!")

                    if payload["function"] == "plug_off":
                        is_plug = False
                        send_message(peer_id, "Заглушка успешно отключена!")

                    if payload["function"] == "chat_on":
                        is_chat = True
                        send_message(peer_id, "Режим чат-бот успешно включён!")

                    if payload["function"] == "chat_off":
                        is_chat = False
                        send_message(
                            peer_id, "Режим чат-бота успешно выключен!")

                except KeyError:
                    pass

                try:
                    payload = JSON.JSONDecoder().decode(object_0["payload"])
                    try:
                        # пробуем достать шаблон
                        t_name = payload["template"]
                        if t_name in templates.keys():
                            if t_name == 'support_0':
                                # тут будет функционал по отправке вопроса в чат администраторов

                                # 1. отправка пользователю сообщения о том, что он может описать свою проблему поподробнее ниже
                                template = templates['support_0']
                                send_message(peer_id, **template)
                            elif t_name == 'support_1':
                                is_problem = True
                                template = templates['support_1']
                                send_message(peer_id, **template)
                            else:
                                template = templates[t_name]
                                send_message(peer_id, **template)
                        elif t_name == 'chatbot_status':
                            # отлавливаем состояние статуса чатботности бота
                            # отправляем сообщение с кнопками включения/выключения состояния чатботности
                            send_message(
                                peer_id, "Режим чат-бота", chat_kb)
                    except KeyError:
                        # пробуем достать текст
                        answer = payload["text"]
                        send_message(peer_id, answer)
                except KeyError:
                    pass

            elif keyboard_work == 0:
                message = "На вашей версии VK не поддерживаются меню-клавиатуры ботов.\nВозможное решение: воспользуйтесь другим устройством."
                send_message(peer_id, message=message)

    except:  # Если возникает ошибка, сообщаем об этом разработчику

        # Также при включённом режиме заглушки отправляем пользователю сообщение о ведении технических работ
        if is_plug:
            send_message(
                peer_id, "Сейчас ведутся технические работы, попробуй повторить попытку позже.")

        message = "Возникла ошибка в системе, пора фиксить :)\n\n" + \
            str(traceback.format_exc())
        send_message(peer_id='368424892', message=message)

    return 'ok'
