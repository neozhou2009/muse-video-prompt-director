# 剧本及导演执行稿逐项交付

先人工对照实际源文件建立独立 `source.json`，按场景/源镜/分画的顺序逐项录入；同一拍的动作、对白、表演、反应、起止状态和声音分别成为独立源项。对白拆拍时，每条需要逐字核对的原句为一个源项；来源定位写文件、场次、镜号及可用行号。未提供的字段不伪造。多个来源冲突或用户授权删改需记录原依据及决定。无对白、空镜和画外表演依实际可见性审查，保留原因，不强行入画。

`source.json` 示例：

```json
{"items":[
  {"id":"S01-performance","source_location":"导演稿 S01 表演","field":"performance","text":"奥利弗先握紧手"},
  {"id":"S01-reaction","source_location":"导演稿 S01 反应","field":"reaction","text":"克莱尔看向他的手"},
  {"id":"S01-dialogue","source_location":"剧本 SC01 对白","field":"dialogue","text":"别动。"}
]}
```

`delivery.json` 单独保存成品正文及逐源项处置：

```json
{"clips":[{"id":"C01","visible_cast":["奥利弗","克莱尔"],"prompt":"奥利弗先握紧手。克莱尔看向他的手。奥利弗说：别动。"}],
 "decisions":[
  {"source_id":"S01-performance","status":"included","reason":"在画表演","evidence":[{"clip_id":"C01","time_window":"0—2秒","excerpt":"奥利弗先握紧手","actors":["奥利弗"]}]},
  {"source_id":"S01-reaction","status":"included","reason":"在画反应","evidence":[{"clip_id":"C01","time_window":"2—3秒","excerpt":"克莱尔看向他的手","actors":["克莱尔"]}]},
  {"source_id":"S01-dialogue","status":"included","reason":"原句","evidence":[{"clip_id":"C01","time_window":"3—5秒","excerpt":"别动。","actors":[]}]}
 ]}
```

字段枚举为 `action`、`dialogue`、`performance`、`reaction`、`opening`、`closing`、`sound`。每项恰有一个处置：`included`、`modified`、`omitted` 或 `not_applicable`，均需理由。`modified` 和 `omitted` 必须记录具体 `user_authorization`；没有用户授权不能借此静默删改。有源对白或动作不能用 `not_applicable` 代替授权删减。`included` 和 `modified` 必须给实际正文片段、段号和片内时间窗；表演/反应须指明在画对象。无对白、画外声、空镜等按实际情况注明，不适用项不附正文证据。

逐字保留的对白如跨段，按播放顺序逐段列证据，各 `excerpt` 串接后须等于源对白原文；每段摘录必须实际出现在对应 `prompt`。其他字段可改写成可拍摄的措辞，但要人工确认语义、时机、动作先后、声音与状态均被保留。用户授权修改时使用 `modified` 并记录授权。

执行：`python scripts/validate_source_delivery.py --source source.json --delivery delivery.json`。运行前人工核对源清单覆盖所有目标场景，运行后核对时间窗、段内先后、可见范围、剪辑取用区间与源语义。工具只检查清单和成品之间的结构与原文证据，不能发现清单本身缺了源内容，也不验证时间数值、语义、模型生成效果或导演创作质量。按实际最终交付正文生成JSON并运行，不能只校验草稿或标题。
