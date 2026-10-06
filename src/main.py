from datetime import datetime

list_feedback = [[0]]
list_message = [[0]]
list_client = [[0]]


def create_feedback(response: str, stage: str, failure: str, message: int):
    feedback = []
    if len(list_feedback[0]) > 1:
        feedback.append(list_feedback[0].pop())
    else:
        list_feedback[0][0] += 1
        feedback.append(list_feedback[0][0])
    feedback.append(int((datetime.now().timestamp())))
    feedback.append(response)
    feedback.append(stage)
    feedback.append(failure)
    feedback.append(message)
    list_feedback.append(feedback)
    print(feedback)


def create_message(
    data: str, client: int, description: str, tags: str, stage: str
):
    message = []
    if len(list_message[0]) > 1:
        message.append(list_message[0].pop())
    else:
        list_message[0][0] += 1
        message.append(list_message[0][0])
    message.append(int((datetime.now().timestamp())))
    message.append(data)
    message.append(client)
    message.append(description)
    message.append(tags)
    message.append(stage)
    list_message.append(message)
    print(message)


def create_client(user_agent: str):
    client = []
    if len(list_client[0]) > 1:
        client.append(list_client[0].pop())
    else:
        list_client[0][0] += 1
        client.append(list_client[0][0])
    client.append(int((datetime.now().timestamp())))
    client.append(user_agent)
    list_client.append(client)
    print(client)


def create(datatype: str):
    match datatype:
        case "feedback":
            create_feedback(
                str(input("response -str-> ")),
                str(input("stage -str-> ")),
                str(input("failure -str-> ")),
                int(input("message -int-> ")),
            )
        case "message":
            create_message(
                str(input("data -str-> ")),
                int(input("client -int-> ")),
                str(input("description -str-> ")),
                str(input("tags -str-> ")),
                str(input("stage -str-> ")),
            )
        case "client":
            create_client(str(input("user_agent -str-> ")))


def datatype_match(datatype: str):
    match datatype:
        case "feedback":
            return list_feedback
        case "message":
            return list_message
        case "client":
            return list_client


def delete_data(datatype: str, uid: int):
    target_list = datatype_match(datatype)
    for item in target_list[1:]:
        if item[0] == uid:
            target_list.pop(target_list.index(item))
            target_list[0].append(uid)
            print(target_list[1:])
            break


def edit_data(item: list, target_list: list):
    dummy = []
    for element in item:
        match element:
            case int():
                user_input = input(f"{element} -int-> ")
                if user_input.isnumeric():
                    user_input = int(user_input)
                else:
                    user_input = ""
            case str():
                user_input = str(input(f"{element} -str-> "))
            case _:
                user_input = input(f"{element} -unk-> ")
        if user_input != "":
            dummy.append(user_input)
        else:
            dummy.append(element)
    print(dummy)
    target_list[target_list.index(item)] = dummy


def edit(datatype: str, uid: int):
    match datatype:
        case "feedback":
            for item in list_feedback[1:]:
                if type(item) != int and item[0] == uid:
                    edit_data(item, list_feedback)
        case "message":
            for item in list_message[1:]:
                if type(item) != int and item[0] == uid:
                    edit_data(item, list_message)
        case "client":
            for item in list_client[1:]:
                if type(item) != int and item[0] == uid:
                    edit_data(item, list_client)


def select_data():
    now = int(datetime.now().timestamp())

    resulting_table = []

    table_mf = []
    table_cmf = []
    table_filtered = []
    for item in list_message[1:]:
        for item_2 in list_feedback[1:]:
            if item[0] == item_2[5]:
                table_mf.append(item.copy())
                table_mf[len(table_mf) - 1].extend(item_2[0:4])

    for item in list_client[1:]:
        for item_2 in table_mf:
            if item[0] == item_2[3]:
                table_cmf.append(item.copy())
                table_cmf[len(table_cmf) - 1].extend(item_2)

    for item in table_cmf:
        if item[4] > now - 5 * 60:
            table_filtered.append(item)

    for item in table_filtered:
        resulting_table.append([item[2], item[12], item[8]])

    return resulting_table


def repl():
    while True:
        match input("command: "):
            case "create":
                create(str(input("datatype: ")))
            case "edit":
                edit(str(input("datatype: ")), int(input("uid: ")))
            case "delete":
                delete_data(str(input("datatype: ")), int(input("uid: ")))
            case "list":
                match str(input("datatype: ")):
                    case "feedback":
                        print(list_feedback[1:])
                    case "message":
                        print(list_message[1:])
                    case "client":
                        print(list_client[1:])
            case "select":
                print(select_data())


if __name__ == "__main__":
    repl()
