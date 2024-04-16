import httplib2
import json
import os
import nltk
import re
import time
import random
import pprint
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from pymystem3 import Mystem


def get_service_sacc():
    """Создание сервисного аккаунта Google"""
    creds_json = os.path.dirname(__file__) + "/creds/mysacc2.json"
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds_service = ServiceAccountCredentials.from_json_keyfile_name(
        creds_json, scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)


# Подключение к Google Sheets
service = get_service_sacc()
sheet = service.spreadsheets()


class FAQ(object):
    def __init__(self, name: str, sheet_link: str, sheet_name="FAQ"):
        self.name = name
        self.sheet_link = sheet_link
        self.sheet_name = sheet_name
        self.sheet_id = self.sheet_link.split('/')[-2]
        # Все данные из листа
        self.all_values = sheet.values().get(spreadsheetId=self.sheet_id,
                                             range=f"{self.sheet_name}!A1:ZZ1000").execute()['values'][2:]

        # массив примитивных названий (юзер сейс)
        self.user_says = [element[0] for element in self.all_values]

        # название шаблона и сообщение от бота
        self.templates = [element[2:4] for element in self.all_values]

        # прямые наименования шаблонов
        self.names_templates = [element[2] for element in self.all_values][:-1]

        # массив кнопок, которые объединяются в клавиатуру
        self.buttons = [element[-1] for element in self.all_values]

        # словарь template с баллами после обработки юс
        self.templates_scores = {
            elem: 0 for elem in self.names_templates if elem}

        # набор терминов, которые встречаются в ключевых словах дисциплин
        self.termines = [
            'android', 'anylogic', 'apache', 'api', 'arduino', 'bash', 'bert',
            'bi', 'bpmn', 'cassandra', 'cnn', 'cpu', 'css', 'csv', 'curl', 'dask',
            'dataframe', 'dax', 'docker', 'erp', 'ethereum', 'excel', 'gan', 'git', 'gitlab',
            'google', 'gpu', 'hadoop', 'haskell', 'hcl', 'html', 'http', 'iot', 'ip', 'java',
            'javascript', 'keras', 'kubernetes', 'libusb', 'linux', 'loss', 'mlops', 'mongodb',
            'mpi', 'neo', 'numpy', 'olap', 'openmp', 'oracle', 'pandas', 'plotly', 'power', 'python',
            'pytorch', 'react', 'sklearn', 'spark', 'sparksql', 'sql', 'sqlalchemy', 'swing', 'sympy',
            'terraform', 'vba', 'vec', 'word', 'xml', 'аврора', 'автоэнкодер', 'анализ', 'апк',
            'архитектура', 'ассемблер', 'банк', 'бд', 'бизнес', 'блокчейн', 'веб', 'вероятность',
            'версия', 'ветка', 'граф', 'датасет', 'запрос', 'игра', 'изображение', 'инс',
            'интеграл', 'классификация', 'кластеризация', 'консоль', 'контейнер', 'кредит', 'матрица',
            'метод', 'множество', 'ндс', 'нейрон', 'облако', 'обучение', 'отчет', 'память',
            'персептрон', 'платеж', 'плк', 'портфель', 'признак', 'приложение', 'процессор', 'разметка',
            'распределение', 'регрессия', 'речь', 'риск', 'робот', 'рынок', 'сайт', 'сервис', 'сеть',
            'скоринг', 'слой', 'смо', 'ставка', 'схема', 'счет', 'тег', 'текст', 'тест', 'тестирование',
            'уравнение', 'учет', 'финтех', 'хозяйство', 'яндекс'
        ]

        # связь шаблонов ключевых слов по дисциплинам
        self.template_to_keywords = {
            element[2]: element[0] for element in self.all_values if 'support' not in element[2]}

        # словарь с аналитическими данными по направлениям
        self.temp_to_name_naprav = {
            "bi": "Бизнес-информатика",
            "ib": "Информационная безопасность",
            "ivt": "Информатика и вычислительная техника",
            "inno": "Инноватика",
            "lingv": "Лингвистика",
            "menedz": "Менеджмент",
            "mechrob": "Мехатроника и робототехника",
            "mkn": "Математика и компьютерные науки",
            "pi": "Прикладная информатика",
            "pinzh": "Программная инженерия",
            "pmi": "Прикладная математика и информатика",
            "turism": "Туризм",
            "econom": "Экономика"
        }

        self.napravs_data = {
            "Бизнес-информатика": {
                "bi2021": 0,
                "bi2022": 0,
                "bi2023": 0
            },
            "Информационная безопасность": {
                "ib2021": 0,
                "ib2022": 0,
                "ib2023": 0
            },
            "Информатика и вычислительная техника": {
                "ivt_2021": 0,
                "ivt_2022": 0,
                "ivt_2023": 0
            },
            "Инноватика": {
                "inno_2021": 0,
                "inno_2022": 0,
                "inno_2023": 0
            },
            "Лингвистика": {
                "lingv_2021": 0,
                "lingv_2022": 0,
                "lingv_2023": 0
            },
            "Менеджмент": {
                "menedz_2021": 0,
                "menedz_2022": 0,
                "menedz_2023": {
                    "analys_menedz_2023": 0,
                    "others_menedz_2023": 0,
                }
            },
            "Мехатроника и робототехника": {
                "mechrob_2021": 0,
                "mechrob_2022": 0,
                "mechrob_2023": 0
            },
            "Математика и компьютерные науки": {
                "mkn2023": 0
            },
            "Прикладная информатика": {
                "pi2021": {
                    "analys_pi2021": 0,
                    "matem_pi2021": 0,
                    "develop_pi2021": 0,
                    "systems_pi2021": 0,
                    "others_pi2021": 0
                },
                "pi2022": {
                    "analys_pi2022": 0,
                    "bigdata_pi2022": 0,
                    "matem_pi2022": 0,
                    "ml_pi2022": 0,
                    "develop_pi2022": 0,
                    "systems_pi2022": 0,
                    "others_pi2022": 0
                },
                "pi2023": {
                    "analys_pi2023": 0,
                    "bigdata_pi2023": 0,
                    "matem_pi2023": 0,
                    "ml_pi2023": 0,
                    "program_pi2023": 0,
                    "develop_pi2023": 0,
                    "apparat_pi2023": 0,
                    "model_pi2023": 0,
                    "po_pi2023": 0,
                    "app_pi2023": 0,
                    "systems_pi2023": 0,
                    "test_pi2023": 0,
                    "fintech_pi2023": 0,
                    "others_pi2023": 0
                }
            },
            "Программная инженерия": {
                "pinzh2023": 0
            },
            "Прикладная математика и информатика": {
                "pmi2021": {
                    "analys_pmi2021": 0,
                    "matem_pmi2021": 0,
                    "others_pmi2021": 0
                },
                "pmi2022": {
                    "analys_pmi2022": 0,
                    "bigdata_pmi2022": 0,
                    "matem_pmi2022": 0,
                    "ml_pmi2022": 0,
                    "others_pmi2022": 0
                },
                "pmi2023": {
                    "analys_pmi2023": 0,
                    "matem_pmi2023": 0,
                    "ml_pmi2023": 0,
                    "develop_pmi2023": 0,
                    "others_pmi2023": 0
                }
            },
            "Туризм": {
                "turism_2021": 0,
                "turism_2022": 0,
                "turism_2023": 0
            },
            "Экономика": {
                "econom_2020": 0,
                "econom_2021": {
                    "analys_econom_2021": 0,
                    "others_econom_2021": 0
                },
                "econom_2022": {
                    "analys_econom_2022": 0,
                    "others_econom_2022": 0
                },
                "econom_2023": {
                    "analys_econom_2023": 0,
                    "others_econom_2023": 0
                }
            }
        }

        self.spheres = list(
            self.flatten(
                [
                    [
                        list(self.napravs_data[naprav][sphere].keys()) for sphere in
                        list(self.napravs_data[naprav].keys()) if self.napravs_data[naprav][sphere] != 0
                    ]
                    for naprav in self.napravs_data.keys()
                ]
            )
        )

    def flatten(self, x):
        if isinstance(x, list):
            for q in x:
                yield from self.flatten(q)
        else:
            yield x

    def render_full_names_templates(self):
        names_templates = list(filter(None, self.names_templates))
        full_names_templates = list(
            filter(None, [element[1] for element in self.all_values]))
        return dict(zip(names_templates, full_names_templates))

    def clean_template_scores(self):
        self.templates_scores = {
            elem: 0 for elem in self.names_templates if elem}

    def clean_napr_sphere_scores(self):
        self.napravs_data = {
            "Бизнес-информатика": {
                "bi2021": 0,
                "bi2022": 0,
                "bi2023": 0
            },
            "Информационная безопасность": {
                "ib2021": 0,
                "ib2022": 0,
                "ib2023": 0
            },
            "Информатика и вычислительная техника": {
                "ivt_2021": 0,
                "ivt_2022": 0,
                "ivt_2023": 0
            },
            "Инноватика": {
                "inno_2021": 0,
                "inno_2022": 0,
                "inno_2023": 0
            },
            "Лингвистика": {
                "lingv_2021": 0,
                "lingv_2022": 0,
                "lingv_2023": 0
            },
            "Менеджмент": {
                "menedz_2021": 0,
                "menedz_2022": 0,
                "menedz_2023": {
                    "analys_menedz_2023": 0,
                    "others_menedz_2023": 0,
                }
            },
            "Мехатроника и робототехника": {
                "mechrob_2021": 0,
                "mechrob_2022": 0,
                "mechrob_2023": 0
            },
            "Математика и компьютерные науки": {
                "mkn2023": 0
            },
            "Прикладная информатика": {
                "pi2021": {
                    "analys_pi2021": 0,
                    "matem_pi2021": 0,
                    "develop_pi2021": 0,
                    "systems_pi2021": 0,
                    "others_pi2021": 0
                },
                "pi2022": {
                    "analys_pi2022": 0,
                    "bigdata_pi2022": 0,
                    "matem_pi2022": 0,
                    "ml_pi2022": 0,
                    "develop_pi2022": 0,
                    "systems_pi2022": 0,
                    "others_pi2022": 0
                },
                "pi2023": {
                    "analys_pi2023": 0,
                    "bigdata_pi2023": 0,
                    "matem_pi2023": 0,
                    "ml_pi2023": 0,
                    "program_pi2023": 0,
                    "develop_pi2023": 0,
                    "apparat_pi2023": 0,
                    "model_pi2023": 0,
                    "po_pi2023": 0,
                    "app_pi2023": 0,
                    "systems_pi2023": 0,
                    "test_pi2023": 0,
                    "fintech_pi2023": 0,
                    "others_pi2023": 0
                }
            },
            "Программная инженерия": {
                "pinzh2023": 0
            },
            "Прикладная математика и информатика": {
                "pmi2021": {
                    "analys_pmi2021": 0,
                    "matem_pmi2021": 0,
                    "others_pmi2021": 0
                },
                "pmi2022": {
                    "analys_pmi2022": 0,
                    "bigdata_pmi2022": 0,
                    "matem_pmi2022": 0,
                    "ml_pmi2022": 0,
                    "others_pmi2022": 0
                },
                "pmi2023": {
                    "analys_pmi2023": 0,
                    "matem_pmi2023": 0,
                    "ml_pmi2023": 0,
                    "develop_pmi2023": 0,
                    "others_pmi2023": 0
                }
            },
            "Туризм": {
                "turism_2021": 0,
                "turism_2022": 0,
                "turism_2023": 0
            },
            "Экономика": {
                "econom_2020": 0,
                "econom_2021": {
                    "analys_econom_2021": 0,
                    "others_econom_2021": 0
                },
                "econom_2022": {
                    "analys_econom_2022": 0,
                    "others_econom_2022": 0
                },
                "econom_2023": {
                    "analys_econom_2023": 0,
                    "others_econom_2023": 0
                }
            }
        }

    def __str__(self):
        final_str = f"Таблица «{self.name}»\n\n"
        final_str += f"Ссылка на таблицу: {self.sheet_link}\n"
        return final_str

    def clean(self, text):
        # преобразуем слово к нижнему регистру
        text_low = text.lower()

        # проверка текста на наличие в нём кода эмодзи вк
        # принцип — если первый символ в тексте слова не буква, то это точно эмодзи!
        if text_low[0].isalpha() == False:
            if text_low[0].isdigit() and len(text_low) == 4:
                return text_low
            else:
                return "тут пустой текст"

        # описываем текстовый шаблон для удаления: "все, что НЕ (^) является буквой \w или пробелом \s"
        re_not_word = r'[^\w\s]'

        # заменяем в исходном тексте то, что соответствует шаблону, на пустой текст (удаляем)
        text_final = re.sub(re_not_word, '', text_low)

        # возвращаем очищенный текст
        return text_final

    def render_templates(self):
        template_dict = {}
        current_name = ""

        for i in range(len(self.buttons)):
            t_name = self.templates[i][0]  # название шаблона
            t_message = self.templates[i][1]  # сообщение для шаблона
            button = self.buttons[i]  # кнопка в шаблоне
            # button = button.replace("'", '"')  # меняем кавычки
            button = json.loads(button)  # переводим строку в json

            if t_name != "":
                current_name = t_name
                template_dict[t_name] = {
                    "message": t_message,
                    "keyboard": {
                        "one_time": False,
                        "inline": False,
                        "buttons": []
                    }
                }

            template_dict[current_name]["keyboard"]["buttons"].append(
                button)  # добавляем кнопку к шаблону

        file_path = f'{os.path.dirname(__file__)}/templates.json'
        if os.path.exists(file_path):
            # Если файл существует, удаляем его
            os.remove(file_path)
            time.sleep(3)

        with open(file_path, 'w', encoding='utf-8') as write_file:
            json.dump(template_dict, write_file, ensure_ascii=False, indent=4)

        return template_dict

    def reshape_self_user_says(self):
        user_says = [us_word.split(", ")
                     for us_word in list(filter(None, self.user_says))]
        return dict(zip(list(filter(None, self.names_templates)), user_says))

    # Получение расстояния Дамерау-Левенштейна между словом пользователя и юс
    def get_levenstein_score(self, us_words, real_word):
        lst_levensteins = []
        for us_word in us_words:
            # применение алгоритма расстояния Дамерау-Левенштейна (использование транспозиции символов при обработке)
            value_levenstein = nltk.edit_distance(
                us_word, real_word, transpositions=True)
            lst_levensteins.append(value_levenstein)
        total_score = min(lst_levensteins)
        return total_score

    # Получение потенциальных шаблонов для всех слов пользователя
    def get_potential_templates(self, real_word):
        templates_scores = self.templates_scores
        user_says = self.reshape_self_user_says()
        for template, us_case in user_says.items():
            new_score_template = self.get_levenstein_score(us_case, real_word)
            templates_scores[template] += new_score_template
        sorted_templates_scores = sorted(
            templates_scores.items(), key=lambda item: item[1])
        self.templates_scores = dict(sorted_templates_scores)
        return [-1, sorted_templates_scores[0][0], sorted_templates_scores[1][0], sorted_templates_scores[2][0],
                sorted_templates_scores[3][0], sorted_templates_scores[4][0]]

    def search_in_one_word(self, user_word):
        results_lst = []
        for index, template_names in enumerate(self.user_says):
            names = template_names.lower().split(", ")
            print(user_word, names)
            if user_word in names:
                results_lst.append(self.templates[index][0])
                # мэтчинг шаблонов по направлениям и сферам деятельности
                # начало подготовки аналитической сводки по ключевому слову
                keyw_t = self.templates[index][0]

                # ищем мэтч сначала по сферам
                for sphere in self.spheres:
                    if sphere in keyw_t:
                        napr_sphere = sphere.split(
                            '_')[-1] if len(sphere.split('_')) == 2 else '_'.join(sphere.split('_')[1:])
                        name_naprav = self.temp_to_name_naprav[napr_sphere[-5::-1][::-1]
                                                               if '_' not in napr_sphere else (napr_sphere.split('_'))[0]]
                        self.napravs_data[name_naprav][napr_sphere][sphere] += 1
                        break

                # потом ищем мэтч по направлениям и сверяемся
                naprav_without_spheres = list(
                    self.flatten(
                        [
                            [n for n in self.napravs_data[napr].keys() if type(
                                self.napravs_data[napr][n]) == int]
                            for napr in self.napravs_data.keys()
                        ]
                    )
                )
                for naprav in naprav_without_spheres:
                    if naprav in keyw_t:
                        name_naprav = self.temp_to_name_naprav[naprav[-5::-1][::-1]
                                                               if '_' not in naprav else (naprav.split('_'))[0]]
                        self.napravs_data[name_naprav][naprav] += 1
                        break

        if len(results_lst) == 0:
            return self.get_potential_templates(user_word)
        elif len(results_lst) < 3:
            random.shuffle(results_lst)
            return [0, results_lst[0]]
        elif len(results_lst) <= 4:
            random.shuffle(results_lst)
            return [3] + results_lst[:3]
        elif len(results_lst) >= 5:
            random.shuffle(results_lst)
            return [5] + results_lst[:5]

    # ПРОПИСАТЬ РУЧКАМИ, КАК БУДЕТ РАБОТАТЬ СИСТЕМА ПОТЕНЦИАЛЬНЫХ ЮС С ВЫВОДОМ INLINE КНОПОК !!!

    def search_user_says(self, user_sentence):
        user_words = [self.clean(
            word) for word in user_sentence.split() if self.clean(word) != ""]
        m = Mystem()
        if len(user_words) == 1:
            return self.search_in_one_word("".join(m.lemmatize(user_words[0])).rstrip('\n'))
        elif len(user_words) > 1:
            list_results = []
            indexes_acc = []
            list_template_values = []

            for index, word in enumerate(user_words):
                result = self.search_in_one_word(
                    "".join(m.lemmatize(word)).rstrip('\n'))
                list_results.append(result[0])
                list_template_values.append(result[1:])
                if result[0] in [0, 3, 5]:
                    indexes_acc.append(index)

            if 0 in list_results or 3 in list_results or 5 in list_results:
                # тогда мы точно говорим о том, что у нас есть точное совпадение

                # Проблема, которая остаётся — мы, заранее прописывая этот алгоритм, никогда не сможем узнать по точным
                # совпадениям, какое конкретно из них имел в виду пользователь, печатая текст боту

                # Как я поступлю в такой ситуации — будет выводиться сообщение, аналогичное ответу о том, что
                # точный ответ на текст пользователя не найден, но бот точно уверен в том, что пользователь сможет
                # найти ответ по inline-кнопкам с шаблонами, по которым найдено точное совпадение

                # ПОДУМАТЬ НАД СМЫСЛОМ ЭТОГО УСЛОВИЯ, потому что из-за него у нас при слове SQL в тексте пользователя
                # выводится чисто первая РПД из рандомно перемешанного списка точно попавших под ключевые слова
                # файлов РПД

                if len(indexes_acc) == 1:
                    # если точное совпадение одно — выводим только его
                    print(list_template_values)
                    print()
                    print()
                    if user_words[indexes_acc[0]] in self.termines:
                        if len(list_template_values[indexes_acc[0]]) == 5:
                            pprint.pprint(self.napravs_data)
                            outp_msg = f"Дисциплины, в которых изучается {user_words[indexes_acc[0]]}, есть на следующих направлениях:\n"
                            res_matching = self.get_count_discs_by_keyword()

                            if res_matching != 'пусто':
                                outp_msg += res_matching
                                print(outp_msg)
                                return (outp_msg, [5, list_template_values[indexes_acc[0]][0], list_template_values[indexes_acc[0]][1], list_template_values[indexes_acc[0]][2], list_template_values[indexes_acc[0]][3], list_template_values[indexes_acc[0]][4]])
                        elif len(list_template_values[indexes_acc[0]]) == 3:
                            pprint.pprint(self.napravs_data)
                            outp_msg = f"Дисциплины, в которых изучается {user_words[indexes_acc[0]]}, есть на следующих направлениях:\n"
                            res_matching = self.get_count_discs_by_keyword()

                            if res_matching != 'пусто':
                                outp_msg += res_matching
                                print(outp_msg)
                                return (outp_msg, [3, list_template_values[indexes_acc[0]][0], list_template_values[indexes_acc[0]][1], list_template_values[indexes_acc[0]][2]])

                    self.templates_scores[list_template_values[indexes_acc[0]][0]] = 0
                    return [0, list_template_values[indexes_acc[0]][0]]

                elif len(indexes_acc) == 2:
                    # если точных совпадений 2
                    if (list_template_values[indexes_acc[0]] != list_template_values[indexes_acc[1]]):
                        # templates разные
                        print(
                            list_template_values[indexes_acc[0]], list_template_values[indexes_acc[1]])
                        return [2, list_template_values[indexes_acc[0]][0], list_template_values[indexes_acc[1]][0]]
                    else:
                        # templates одинаковые
                        return [0, list_template_values[indexes_acc[0]][0]]
                else:
                    # если точных совпадений несколько — будем выводить топ-5

                    # кейс с повторными точными совпадениями мы избегаем циклом ниже, потому что обнуляем значение по
                    # одному и тому же ключу
                    for index_acc in indexes_acc:
                        accurate_template = list_template_values[index_acc][0]
                        self.templates_scores[accurate_template] = 0

                    sorted_templates_scores = sorted(
                        self.templates_scores.items(), key=lambda item: item[1])
                    self.templates_scores = dict(sorted_templates_scores)

                    # код, который более понятно показывает картину обработки данных словаря баллов template & scores
                    keys_sorted = list(self.templates_scores.keys())
                    values_sorted = list(self.templates_scores.values())

                    # если получается такая ситуация, что у нас оказалось 5 и более одинаковых по названию точных
                    # совпадения, то мы меняем индикатор на 0 и просто выводим первую пару
                    # в отсортированном словаре template & scores
                    if values_sorted[0] == 0 and (values_sorted[1] > 0):
                        return [0, keys_sorted[0]]

                    # кейс, когда 2 точных совпадения, частота встречи которых выше чем 1 раз
                    # тип когда эта пара точных совпадений встречается у нас больше чем 1 раз
                    elif values_sorted[0] == values_sorted[1] == 0 and (values_sorted[2] > 0):
                        return [2, keys_sorted[0], keys_sorted[1]]

                    elif values_sorted[0] == values_sorted[1] == values_sorted[2] == 0 and (values_sorted[3] > 0):
                        return [3, keys_sorted[0], keys_sorted[1], keys_sorted[2]]

                    # во всех остальных кейсах - выводим топ-5
                    else:
                        return [5, keys_sorted[0], keys_sorted[1], keys_sorted[2], keys_sorted[3], keys_sorted[4]]

            else:
                # если точных совпадений нет, то мы берём самое актуальное состояние template_scores
                # и выводим -1 вместе с последним результатом вызова функции potential_templates

                return [-1] + list_template_values[-1]

    def get_count_discs_by_keyword(self):
        final_lst = []
        for key, value in list(self.napravs_data.items()):
            types_values = [type(elem) == int for elem in list(value.values())]
            # фильтруем вложенные словари с данными сфер от обычных списков с данными направлений
            if sum(types_values) == len(types_values):
                if sum(list(value.values())) == 0:
                    continue
                else:
                    total_value = sum(
                        dict(self.napravs_data[key].items()).values())
                    if total_value == 0:
                        continue
                    else:
                        if 10 <= int(str(total_value)[-2:]) <= 20:
                            kword_str = 'дисциплин'
                        else:
                            kword_dct = {1: 'дисциплина', 2: 'дисциплины',
                                         3: 'дисциплины', 4: 'дисциплины', 5: 'дисциплин'}
                            kword_str = kword_dct[int(
                                str(total_value)[-1])] if int(str(total_value)[-1]) <= 5 else kword_dct[5]

                    final_lst.append(f'– «{key}» ({total_value} {kword_str})')

            else:
                # делим кейс на ситуации, когда 1 словарь и когда словарей с данными больше 1
                if types_values.count(False) == 1:
                    ind_dict = types_values.index(False)
                    total_value = 0
                    if ind_dict == (len(types_values) - 1):
                        total_value += sum(list(value.values())[:ind_dict])
                    else:
                        total_value += sum(list(value.values())
                                           [:ind_dict] + list(value.values())[ind_dict+1:])
                    total_value += sum(list(list(value.values())
                                       [ind_dict].values()))
                    if total_value == 0:
                        continue
                    else:
                        if 10 <= int(str(total_value)[-2:]) <= 20:
                            kword_str = 'дисциплин'
                        else:
                            kword_dct = {1: 'дисциплина', 2: 'дисциплины',
                                         3: 'дисциплины', 4: 'дисциплины', 5: 'дисциплин'}
                            kword_str = kword_dct[int(
                                str(total_value)[-1])] if int(str(total_value)[-1]) <= 5 else kword_dct[5]

                        final_lst.append(
                            f'– «{key}» ({total_value} {kword_str})')

                else:
                    data_values = [value for value in list(
                        value.values()) if value != 0]
                    total_value = sum([elem if type(elem) == int else sum(
                        elem.values()) for elem in data_values])
                    if total_value == 0:
                        continue
                    else:
                        if 10 <= int(str(total_value)[-2:]) <= 20:
                            kword_str = 'дисциплин'
                        else:
                            kword_dct = {1: 'дисциплина', 2: 'дисциплины',
                                         3: 'дисциплины', 4: 'дисциплины', 5: 'дисциплин'}
                            kword_str = kword_dct[int(
                                str(total_value)[-1])] if int(str(total_value)[-1]) <= 5 else kword_dct[5]

                    final_lst.append(f'– «{key}» ({total_value} {kword_str})')

        if len(final_lst) > 0:
            return '\n'.join(final_lst)
        else:
            return 'пусто'

    def get_templates(self):
        try:
            with open(f"{os.path.dirname(__file__)}/templates.json", 'r', encoding='utf-8') as read_file:
                templates = json.load(read_file)
        except (FileNotFoundError, json.decoder.JSONDecodeError, TypeError):
            templates = {}

        return templates


faq_table = FAQ(name="FAQ система",
                sheet_link="https://docs.google.com/spreadsheets/d/1iYKz7fNpviX2r15v7QNlcYbYan2MGYqonytu05RDh6c/edit#gid=0")

print(faq_table.search_user_says(
    'хочу посмотреть дисциплины по прикладной математике и информатике, гоу?'))
# pprint.pprint(faq_table.template_to_keywords)

# кейсы
# я хочу перейти в главное меню
# я хочу узнать дисциплину про python
# расскажи мне что-нибудь про sql
# я хочу видеть дисциплины 2021 года
# про 2021
# хочу поступить на прикладную информатику, покажи мне дисциплины
# меня интересует иб, покажи дисциплины
