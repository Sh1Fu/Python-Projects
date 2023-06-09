import argparse as arg
import json
import os
import re
from urllib.parse import quote

import matplotlib.pyplot as plt
import requests as req


class ScheduleFindError(Exception):
    '''
    Default own Exception
    '''

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        string = '''Не удалось найти расписание по параметру.
Проверьте введенное значение'''
        return string


class RequestSender:
    '''
    A class with some functionality that allows you to find data about
    teachers and about the group, as well as to get the
    timetable by parameters in raw form
    '''

    def __init__(self, teacher_name: str, group_id: str, date: str, place: str) -> None:
        self.ENDPOINTS = {
            "group": "https://ruz.spbstu.ru/search/groups?q=",
            "teacher": "https://ruz.spbstu.ru/search/teacher?q=",
            "teacher_schedule": "https://ruz.spbstu.ru/teachers/"
        }
        self.teacher_name = teacher_name
        self.group_id = group_id
        self.date = date
        self.place = place

    def date_format(self) -> str:
        '''
        Formatting the date according to its type in the query
        '''
        try:
            date_raw = self.date.split('.')
            return f"{date_raw[2]}-{date_raw[1]}-{date_raw[0]}"
        except AttributeError:
            return ""

    def find_group(self) -> tuple:
        '''
        Finding the group id for queries and the faculty id.\n
        Important! The id of the faculty is a necessary parameter,\n
        because it participates in the formation of the link in the query
        '''
        response = req.get(
            self.ENDPOINTS['group'] + quote(self.group_id, safe=''))
        data = self.extract_initial_state(response)
        if len(data["searchGroup"]["data"]) == 1:
            return (
                data["searchGroup"]["data"][0]["faculty"]["id"],
                data["searchGroup"]["data"][0]["id"]
            )
        else:
            return (-1, -1)

    def find_teacher(self) -> int:
        '''
        Finding a teacher's id by FULL NAME (last name, first name, patronymic)
        '''
        resp = req.get(self.ENDPOINTS['teacher'] +
                       quote(self.teacher_name, safe=''))
        data = self.extract_initial_state(resp)
        if len(data['searchTeacher']['data']) == 1:
            return data['searchTeacher']['data'][0]['id']
        else:
            return -1

    def find_place(self) -> tuple:
        '''
        Optional task. Use ``api/v1/ruz/buildings`` for json
        '''
        pass

    def extract_initial_state(self, data: req.Response) -> dict:
        '''
        Extract all data from HTML response
        '''
        return json.loads(re.findall(r"\{\"faculties\".+", data.text)[0][:-2])

    def get_teacher_schedule(self) -> dict:
        '''
        Get a raw teacher's schedule by his own id
        '''
        teacher_id = self.find_teacher()
        if teacher_id == -1:
            raise ScheduleFindError
        resp = req.get(self.ENDPOINTS['teacher_schedule'] +
                       str(teacher_id) + "?date=" + self.date_format())
        data = self.extract_initial_state(resp)
        return data['teacherSchedule']['data'][str(teacher_id)]

    def get_group_schedule(self) -> dict:
        '''
        Get a raw group's schedule by his own id
        '''
        g_info = self.find_group()
        if g_info[1] == -1:
            raise ScheduleFindError
        resp = req.get(
            f"https://ruz.spbstu.ru/faculty/{g_info[0]}/groups/{g_info[1]}?date={self.date_format()}")
        data = self.extract_initial_state(resp)
        return data['lessons']['data'][str(g_info[1])]


class ParseSchedule(RequestSender):
    '''
    Standard class with custom schedule output,\n
    where there is the minimum necessary information
    '''

    def __init__(self, args: arg.Namespace) -> None:
        super().__init__(teacher_name=args.t,
                         group_id=args.g,
                         date=args.d,
                         place=args.a)
        self.WEEKDAYS = {
            1: "Понедельник",
            2: "Вторник",
            3: "Среда",
            4: "Четверг",
            5: "Пятница",
            6: "Суббота",
            7: "Воскресенье"
        }
        self.mode = 'teacher' if args.m == 1 else 'group'

    def print_schedule(self) -> dict:
        '''
        Beautiful output of the schedule
        according to the selected mode of the script
        '''
        graph_info = dict()
        match self.mode:
            case 'teacher':
                print(self.teacher_name)
                raw_schedule = self.get_teacher_schedule()
                for day in raw_schedule:
                    print(
                        f"======== {self.WEEKDAYS[day['weekday']]} ========\n")
                    for lesson in day['lessons']:
                        try:
                            graph_info[day['date']] += 1
                        except KeyError:
                            graph_info[day['date']] = 1
                        print(
                            f"{lesson['time_start']} - {lesson['time_end']}:")
                        print(f"    {lesson['subject']}")
                        print(f"    {lesson['typeObj']['name']}")
                        if lesson['additional_info'] == "Поток":
                            print(
                                f"    Поток, {lesson['groups'][0]['level']} курс {lesson['groups'][0]['faculty']['abbr']}")
                        else:
                            print(f"    Группа {lesson['groups'][0]['name']}")
                        print(
                            f"    Аудитория {lesson['auditories'][0]['name']}, {lesson['auditories'][0]['building']['name']}")
                    print("\n")
            case 'group':
                print(self.group_id)
                raw_schedule = self.get_group_schedule()
                for day in raw_schedule:
                    print(
                        f"======== {self.WEEKDAYS[day['weekday']]} ========\n")
                    for lesson in day['lessons']:
                        try:
                            graph_info[day['date']] += 1
                        except KeyError:
                            graph_info[day['date']] = 1
                        print(
                            f"{lesson['time_start']} - {lesson['time_end']}:")
                        print(f"    {lesson['subject']}")
                        print(f"    {lesson['typeObj']['name']}")
                        if (lesson['teachers']):
                            print(f"    {lesson['teachers'][0]['full_name']}")
                        print(
                            f"    Аудитория {lesson['auditories'][0]['name']}, {lesson['auditories'][0]['building']['name']}")
                    print("\n")
        return graph_info

    def draw_graph(self) -> None:
        '''
        Prepare data from raw schedule and draw the bar
        thanks by modified dates and counts
        '''
        data = self.print_schedule()
        count_of_subjects = list(data.values())
        dates = [raw_date[5:] for raw_date in list(data.keys())]
        plt.bar(dates, count_of_subjects, width=0.4)
        plt.title(f"Количество занятий каждый день с {dates[0]}")
        plt.autoscale(enable=True)
        plt.xlabel("День недели")
        plt.ylabel("Количество занятий")
        os.makedirs('result') if not os.path.exists('result') else None
        plt.savefig(f'result/schedule_{dates[0]}.png')


def main():
    parser = arg.ArgumentParser(prog="Polytech Python Schedule",
                                description="A Python script to parse Polytech schedule by teacher name or group id")
    parser.add_argument(
        "-m", type=int, help="Select mode to work: 1 - work with teacher name, 2 - parse by group id", choices=[1, 2], required=True)
    parser.add_argument("-t", type=str, help="Teacher name")
    parser.add_argument("-g", type=str, help="University group ID")
    parser.add_argument("-d", type=str, help="The date you are interested in")
    parser.add_argument("-a", type=str, help="The number of place")

    args = parser.parse_args()
    schedule = ParseSchedule(args=args)
    schedule.draw_graph()


if __name__ == "__main__":
    main()
