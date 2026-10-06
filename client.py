import socket

HOST = "127.0.0.1"
PORT = 9090
FIELD_COUNTS = {"feedback": 6, "message": 7, "client": 3}


class RpcClient:

    def send_create_feedback(self):
        buffer = ""
        buffer += "<response>" + str(input("response: ")) + "</response>"
        buffer += "<stage>" + str(input("stage: ")) + "</stage>"
        buffer += "<failure>" + str(input("failure: ")) + "</failure>"
        buffer += "<message>" + str(input("message: ")) + "</message>"
        return buffer

    def send_create_message(self):
        buffer = ""
        buffer += "<data>" + str(input("data: ")) + "</data>"
        buffer += "<client>" + str(input("client: ")) + "</client>"
        buffer += (
            "<description>" + str(input("description: ")) + "</description>"
        )
        buffer += "<tags>" + str(input("tags: ")) + "</tags>"
        buffer += "<stage>" + str(input("stage: ")) + "</stage>"
        return buffer

    def send_create_client(self):
        buffer = ""
        buffer += "<user_agent>" + str(input("user_agent: ")) + "</user_agent>"
        return buffer

    def send_edit_data(self):
        buffer = ""
        datatype = input("datatype: ")
        buffer += "<datatype>" + datatype + "</datatype>"
        buffer += "<uid>" + input("uid: ") + "</uid>"
        count = FIELD_COUNTS.get(datatype, 0)
        for i in range(count):
            buffer += "<value>" + input(f"value[{i}]: ") + "</value>"
        return buffer

    def send_select_data(self):
        return ""

    def code_convert(self, op_code):
        match op_code:
            case "1":
                return self.send_create_feedback()
            case "2":
                return self.send_create_message()
            case "3":
                return self.send_create_client()
            case "4":
                return self.send_edit_data()
            case "5":
                return self.send_select_data()
            case _:
                return ""

    def start_client(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            print("connected!")
            while True:
                body_size = input("size: ").zfill(5)
                op_code = input("code: ")
                body_data = self.code_convert(op_code)
                msg = (
                    body_size
                    + op_code
                    + "<request>"
                    + body_data
                    + "</request>"
                )
                print(msg)
                sock.sendall(msg.encode("utf-8"))
                data = sock.recv(1024)
                print(data.decode("utf-8"))


if __name__ == "__main__":
    client = RpcClient()
    client.start_client()
