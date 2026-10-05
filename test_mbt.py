import xml.etree.ElementTree as ET
from datetime import datetime
from xml.sax.saxutils import escape

from hypothesis import HealthCheck, settings, strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    rule,
    run_state_machine_as_test,
)

import main
import server

text_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-",
    min_size=1,
    max_size=20,
)

def xml_body(tag_values):
    parts = []
    for tag, value in tag_values:
        parts.append(f"<{tag}>{escape(str(value))}</{tag}>")
    return "<request>" + "".join(parts) + "</request>"

class Model:
    def __init__(self):
        self.client = []
        self.message = []
        self.feedback = []
        self.client_pool = [0]
        self.message_pool = [0]
        self.feedback_pool = [0]

    @staticmethod
    def _take(pool):
        if len(pool) > 1:
            return pool.pop()
        pool[0] += 1
        return pool[0]

    def take_client_uid(self):
        return self._take(self.client_pool)

    def take_message_uid(self):
        return self._take(self.message_pool)

    def take_feedback_uid(self):
        return self._take(self.feedback_pool)

    def seed_pool(self, uid):
        self.client_pool.append(uid)
        self.message_pool.append(uid)
        self.feedback_pool.append(uid)

    def find_client(self, uid):
        for rec in self.client:
            if rec[0] == uid:
                return rec
        return None

    def find_message(self, uid):
        for rec in self.message:
            if rec[0] == uid:
                return rec
        return None

    def find_feedback(self, uid):
        for rec in self.feedback:
            if rec[0] == uid:
                return rec
        return None

    def apply_edit(self, rec, values):
        for i, value in enumerate(values):
            if i >= len(rec) or value in ("", None):
                continue
            if isinstance(rec[i], int):
                try:
                    rec[i] = int(value)
                except (ValueError, TypeError):
                    continue
            else:
                rec[i] = value
        return rec

    def select(self):
        now = int(datetime.now().timestamp())
        rows = []
        for client in self.client:
            for message in self.message:
                if message[1] <= now - 300:
                    continue
                for feedback in self.feedback:
                    if message[3] == client[0] and feedback[5] == message[0]:
                        rows.append([client[2], feedback[2], message[5]])
        return rows

class RPCStateMachine(RuleBasedStateMachine):
    clients = Bundle("clients")
    messages = Bundle("messages")
    feedbacks = Bundle("feedbacks")

    def __init__(self):
        super().__init__()
        main.list_client = [[0]]
        main.list_message = [[0]]
        main.list_feedback = [[0]]
        self.model = Model()

    @rule(target=clients, user_agent=text_strategy)
    def create_client(self, user_agent):
        body = xml_body([("user_agent", user_agent)])
        result = server.execute("3", body)

        expected_uid = self.model.take_client_uid()
        assert result[0] == expected_uid
        assert result[2] == user_agent

        self.model.client.append(list(result))

        reply = server.create_reply("3", result)
        root = ET.fromstring(reply)
        assert root.findtext("uid") == str(expected_uid)

        full = str(len(body)).zfill(5) + "3" + body
        assert server.read(full) == (str(len(body)).zfill(5), "3", body)

        return expected_uid

    @rule(
        target=messages,
        client=clients,
        data=text_strategy,
        description=text_strategy,
        tags=text_strategy,
        stage=text_strategy,
    )
    def create_message(self, client, data, description, tags, stage):
        body = xml_body(
            [
                ("data", data),
                ("client", client),
                ("description", description),
                ("tags", tags),
                ("stage", stage),
            ]
        )
        result = server.execute("2", body)

        expected_uid = self.model.take_message_uid()
        assert result[0] == expected_uid
        assert result[2] == data
        assert result[3] == client
        assert result[4] == description
        assert result[5] == tags
        assert result[6] == stage

        self.model.message.append(list(result))

        reply = server.create_reply("2", result)
        root = ET.fromstring(reply)
        assert root.findtext("uid") == str(expected_uid)

        return expected_uid

    @rule(
        target=feedbacks,
        message=messages,
        response=text_strategy,
        stage=text_strategy,
        failure=text_strategy,
    )
    def create_feedback(self, message, response, stage, failure):
        body = xml_body(
            [
                ("response", response),
                ("stage", stage),
                ("failure", failure),
                ("message", message),
            ]
        )
        result = server.execute("1", body)

        expected_uid = self.model.take_feedback_uid()
        assert result[0] == expected_uid
        assert result[2] == response
        assert result[3] == stage
        assert result[4] == failure
        assert result[5] == message

        self.model.feedback.append(list(result))

        reply = server.create_reply("1", result)
        root = ET.fromstring(reply)
        assert root.findtext("uid") == str(expected_uid)

        return expected_uid

    @rule()
    def simulate_delete(self):
        uid = 9000
        main.list_client[0].append(uid)
        main.list_message[0].append(uid)
        main.list_feedback[0].append(uid)
        self.model.seed_pool(uid)

    @rule(client=clients, user_agent=text_strategy)
    def edit_client(self, client, user_agent):
        values = ["", "", user_agent, "extra"]
        body = xml_body(
            [("datatype", "client"), ("uid", client)]
            + [("value", v) for v in values]
        )
        result = server.execute("4", body)

        rec = self.model.find_client(client)
        assert rec is not None
        self.model.apply_edit(rec, values)
        assert result == rec

        reply = server.create_reply("4", result)
        assert "<item>" in reply

    @rule(
        message=messages,
        data=text_strategy,
        new_client=st.one_of(st.integers(min_value=0, max_value=100), text_strategy),
        description=text_strategy,
        tags=text_strategy,
        stage=text_strategy,
    )
    def edit_message(self, message, data, new_client, description, tags, stage):
        values = ["", "", data, new_client, description, tags, stage, "extra"]
        body = xml_body(
            [("datatype", "message"), ("uid", message)]
            + [("value", v) for v in values]
        )
        result = server.execute("4", body)

        rec = self.model.find_message(message)
        assert rec is not None
        self.model.apply_edit(rec, values)
        assert result == rec

        server.create_reply("4", result)

    @rule(
        feedback=feedbacks,
        response=text_strategy,
        stage=text_strategy,
        failure=text_strategy,
        new_message=st.one_of(st.integers(min_value=0, max_value=100), text_strategy),
    )
    def edit_feedback(self, feedback, response, stage, failure, new_message):
        values = ["", "", response, stage, failure, new_message, "extra"]
        body = xml_body(
            [("datatype", "feedback"), ("uid", feedback)]
            + [("value", v) for v in values]
        )
        result = server.execute("4", body)

        rec = self.model.find_feedback(feedback)
        assert rec is not None
        self.model.apply_edit(rec, values)
        assert result == rec

        server.create_reply("4", result)

    @rule(message=messages)
    def edit_message_created_old(self, message):
        values = ["", "0", "", "", "", "", "", "extra"]
        body = xml_body(
            [("datatype", "message"), ("uid", message)]
            + [("value", v) for v in values]
        )
        result = server.execute("4", body)

        rec = self.model.find_message(message)
        assert rec is not None
        self.model.apply_edit(rec, values)
        assert result == rec

        server.create_reply("4", result)

    @rule(
        datatype=st.sampled_from(["feedback", "message", "client"]),
        uid=st.integers(min_value=1000, max_value=2000),
    )
    def edit_missing(self, datatype, uid):
        body = xml_body([("datatype", datatype), ("uid", uid), ("value", "")])
        result = server.execute("4", body)
        assert result == ""

        reply = server.create_reply("4", result)
        assert "item not found" in reply

    @rule()
    def select(self):
        body = "<request></request>"
        result = server.execute("5", body)
        expected = self.model.select()
        assert result == expected
        server.create_reply("5", result)

    @rule()
    def invalid_op(self):
        result = server.execute("9", "<request></request>")
        assert result == ""
        assert server.create_reply("9", result) == ""

    @rule()
    def read_checks(self):
        body = "<request><x>1</x></request>"
        full = str(len(body)).zfill(5) + "1" + body
        assert server.read(full) == (str(len(body)).zfill(5), "1", body)

        full = "00005" + "1" + "<bad"
        assert server.read(full) is None

        body = "<foo></foo>"
        full = str(len(body)).zfill(5) + "1" + body
        assert server.read(full) is None

    @rule()
    def reply_errors(self):
        assert (
            server.create_reply("1", None)
            == "<reply><error>empty</error></reply>"
        )
        assert (
            server.create_reply("1", [])
            == "<reply><error>shape mismatch</error></reply>"
        )
        assert (
            server.create_reply("2", None)
            == "<reply><error>empty</error></reply>"
        )
        assert (
            server.create_reply("3", [1, 2])
            == "<reply><error>shape mismatch</error></reply>"
        )

    @invariant()
    def state_matches_model(self):
        assert main.list_client[1:] == self.model.client
        assert main.list_message[1:] == self.model.message
        assert main.list_feedback[1:] == self.model.feedback

def test_rpc_mbt():
    run_state_machine_as_test(
        RPCStateMachine,
        settings=settings(
            max_examples=200,
            stateful_step_count=40,
            deadline=None,
            suppress_health_check=[
                HealthCheck.filter_too_much,
                HealthCheck.too_slow,
            ],
        ),
    )
