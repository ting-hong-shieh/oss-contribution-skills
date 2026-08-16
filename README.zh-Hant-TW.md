# OSS Contribution Skills

這是一套給 coding agents 使用的開源貢獻協議。目標不是大量掃 issue、快速開 PR，而是：

> **用更少、更乾淨、證據更完整的貢獻，降低 maintainer 的 review burden。**

## 三個 skills

| Skill | 核心問題 | 預設權限 |
| --- | --- | --- |
| `oss-radar` | 這個工作現在值得做、能做、沒有明顯競爭，而且 upstream 想要嗎？ | READ |
| `oss-contribute` | 如何 reproduce、最小實作、測試、對抗式審查並準備 Draft PR？ | READ + 已批准的 LOCAL |
| `oss-pr-maintenance` | PR 開出後發生了什麼變化？最小正確下一步是什麼？ | READ |

## 核心設計

每一個 contribution case 同時記錄四條軸：

```yaml
work_state: CLAIMS_VERIFIED
upstream_state: DRAFT_OPEN
queue_state: WAITING_UPSTREAM
authority_state: READ_ONLY
```

`DRAFT_OPEN` 不等於 `READY_FOR_REVIEW`。預設同一個 upstream repository 同時最多只有一個 Ready PR；其餘工作可以留在本地或 Draft。

所有數字、百分比、benchmark、完整性與保證性聲稱都必須先建立 Claim–Evidence Matrix。證據不足時，要縮小、加限制或刪除聲稱，不能只把句子寫得更漂亮。

## 自動化邊界

系統可以高度自動化搜尋、讀取、監控、本地實作、測試、self-review、adversarial review 與 PR 草稿準備。但 `push`、開 PR、留言、轉 Ready、close 或 merge 都需要 durable case 裡的精確權限，並通過 head SHA、lease、review capacity 與 evidence gates。

## 驗證

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_repo.py
```

目前 v0.1 是 protocol foundation。`oss-radar` 最成熟；另外兩個 skill 與 Claude/Codex adapters 採保守預設，未授權時會拒絕公開動作。
