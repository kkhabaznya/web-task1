import socket
import main
import xml.etree.element_tree as element_tree

HOST = "127.0.0.1"
PORT = 9090


def log(direction: str, payload) -> None:
    """Печатает в консоль одну строку лога."""
    print(f"[{direction}] {payload}")


def read(data):
    try:
        body_size = data[0:5]
        op_code = data[5]
        body = data[6 : 6 + int(body_size)]
        element_tree.fromstring(body)
        if "<request>" not in body or "</request>" not in body:
            raise ValueError("no request tags")
    except Exception:
        return None
    return body_size, op_code, body


def execute(op_code, body):
    root = element_tree.fromstring(body)
    buffer = [item.text for item in root]
    match op_code:
        case "1":
            return main.create_feedback(
                buffer[0], buffer[1], buffer[2], int(buffer[3])
            )
        case "2":
            return main.create_message(
                buffer[0], int(buffer[1]), buffer[2], buffer[3], buffer[4]
            )
        case "3":
            return main.create_client(buffer[0])
        case "4":
            return main.edit_data(buffer[0], int(buffer[1]), buffer[2:])
        case "5":
            return main.select_data()
        case _:
            return ""


def _flat_reply(names, values):
    if values is None or values == "":
        return "<error>empty</error>"
    if len(names) != len(values):
        return "<error>shape mismatch</error>"
    return "".join(f"<{n}>{v}</{n}>" for n, v in zip(names, values))


def create_reply(op_code, result):
    buffer = "<reply>"
    match op_code:
        case "1":
            buffer += _flat_reply(
                ["uid", "created", "response", "stage", "failure", "message"],
                result,
            )
        case "2":
            buffer += _flat_reply(
                [
                    "uid",
                    "created",
                    "data",
                    "client",
                    "description",
                    "tags",
                    "stage",
                ],
                result,
            )
        case "3":
            buffer += _flat_reply(["uid", "created", "user_agent"], result)
        case "4":
            if not result:
                buffer += "<error>item not found</error>"
            else:
                buffer += "<item>"
                for element in result:
                    buffer += f"<value>{element}</value>"
                buffer += "</item>"
        case "5":
            buffer = ""
            for row in result:
                user_agent, response, tags = row
                buffer += (
                    "<row>"
                    f"<user_agent>{user_agent}</user_agent>"
                    f"<response>{response}</response>"
                    f"<tags>{tags}</tags>"
                    "</row>"
                )
        case _:
            return ""
    return buffer + "</reply>"


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        server_sock.listen(1)
        log("INFO", f"listening on {HOST}:{PORT}")

        conn, addr = server_sock.accept()
        with conn:
            log("INFO", f"connected from {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    log("INFO", "client closed")
                    break

                raw = data.decode("utf-8")
                log("IN ", raw)

                parsed = read(raw)
                if parsed is None:
                    log("WARN", "bad request (failed to parse)")
                    err = "<reply><error>bad request</error></reply>"
                    packet = "00" + str(len(err)).zfill(4) + err
                    log("OUT", packet)
                    conn.sendall(packet.encode("utf-8"))
                    continue

                body_size, op_code, body = parsed
                log(
                    "PARSE",
                    f"op_code={op_code} body_size={body_size} body={body}",
                )

                exec_result = execute(op_code, body)
                log("EXEC", f"op_code={op_code} -> {exec_result}")

                xml = create_reply(op_code, exec_result)
                response = op_code.zfill(2) + str(len(xml)).zfill(4) + xml
                log("OUT", response)
                conn.sendall(response.encode("utf-8"))


if __name__ == "__main__":
    start_server()
