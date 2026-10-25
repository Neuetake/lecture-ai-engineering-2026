from types import SimpleNamespace

from app import ask as ask_module


class FakeChat:
    def __init__(self):
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        return SimpleNamespace(
            text=f"answer to {question}",
            usage_metadata=SimpleNamespace(
                prompt_token_count=2,
                candidates_token_count=3,
            ),
        )


class FakeClient:
    def __init__(self, api_key):
        self.chats = self
        self.created_chats = []

    def create(self, model):
        chat = FakeChat()
        self.created_chats.append(chat)
        return chat


def test_main_keeps_history_and_starts_new_chat(monkeypatch, capsys):
    clients = []

    def create_client(api_key):
        client = FakeClient(api_key)
        clients.append(client)
        return client

    inputs = iter(["follow-up", "/new", "new topic", "/exit"])
    monkeypatch.setattr(ask_module.genai, "Client", create_client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr("sys.argv", ["app.ask", "first question"])

    ask_module.main()

    assert len(clients[0].created_chats) == 2
    assert clients[0].created_chats[0].questions == ["first question", "follow-up"]
    assert clients[0].created_chats[1].questions == ["new topic"]
    output = capsys.readouterr().out
    assert output.count("[トークン数] 入力: 2 / 出力: 3") == 3
