# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
LLMを２回呼び出す。
用語集を検索してから答える

- `--trace` で見えたツール呼び出し（ツール名と引数）：
--- trace ---
[tool call]   get_lecture_summary({'lecture': 2})
[tool return] get_lecture_summary -> # 第2回 ファインチューニングとLoRA
[usage] RunUsage(cost=Decimal('0.0008596'), details={'text_prompt_tokens': 1182}, input_text_tokens=1182, input_tokens=1182, output_tokens=202, requests=2, tool_calls=1)

- 1つの質問での LLM 呼び出し回数（`requests`）：２回

- 追加したツールと、docstring に書いた説明：
追加したツール：make_quiz
docstring：
"""指定した回の用語から 1つを選び、確認問題と答えを返す。

「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
"""

## 宿題

- 取り組んだレベル：実装

- やったこと：学習の記録を learning_log/ フォルダに保存するツール save_learning_log を作った。
保存の前に利用者の確認を挟んだ（Pydantic AI の requires_approval=True）

- 結果：
 run python -m app.agent --trace "第2回を復習したことを学習ログに保存してください。"
[model] gemini-3.5-flash-lite
save_learning_log を実行してよいですか？ [y/N]: y
第2回の復習を学習ログに保存しました！

引き続き、第2回の内容や気になる用語について質問があればいつでもお知らせください。

関連：第2回

--- trace ---
[tool call]   save_learning_log({'log_entry': {'content': '第2回を復習した', 'lecture': 2}})
[tool return] save_learning_log -> 学習ログを保存しました。現在のログ件数: 1…
[usage] RunUsage(cost=Decimal('0.0002288'), details={'text_prompt_tokens': 471}, input_text_tokens=471, input_tokens=471, output_tokens=35, requests=1, tool_calls=1)

- 気づき・疑問：
ツールが呼ばれても、利用者が許可するまでは実際の保存処理が行われないことを確認できた。

許可した後、ちゃんとlearning_logフォルダにjsonファイルとして学習ログが保存されていることを確認できた。