"""Validate a reviewed source inventory against actual compiled prompt text."""
import argparse
import json
from pathlib import Path

FIELDS = {'action', 'dialogue', 'performance', 'reaction', 'opening', 'closing', 'sound'}


def validate(source, delivery):
    items = source.get('items')
    clips = delivery.get('clips')
    decisions = delivery.get('decisions')
    if not isinstance(items, list) or not items or not isinstance(clips, list) or not clips or not isinstance(decisions, list):
        raise ValueError('需要非空源项清单、生成段和处置清单')
    def indexed(rows, label):
        result = {}
        for row in rows:
            key = row.get('id')
            if not isinstance(key, str) or not key.strip() or key in result:
                raise ValueError(f'{label} ID 缺失或重复: {key}')
            result[key] = row
        return result
    src = indexed(items, '源项')
    by_clip = indexed(clips, '生成段')
    by_item = {}
    for d in decisions:
        key = d.get('source_id')
        if key not in src or key in by_item:
            raise ValueError(f'处置项无源项或重复: {key}')
        by_item[key] = d
    if set(src) != set(by_item):
        raise ValueError(f'源项缺少处置: {sorted(set(src) - set(by_item))}')
    order = {c['id']: i for i, c in enumerate(clips)}
    for c in clips:
        if not isinstance(c.get('prompt'), str) or not c['prompt'].strip():
            raise ValueError(f"{c['id']}: 成品正文为空")
        cast = c.get('visible_cast')
        if not isinstance(cast, list) or any(not isinstance(a, str) or not a.strip() for a in cast):
            raise ValueError(f"{c['id']}: 需提供在画人物列表")
    for item in items:
        sid = item['id']; field = item.get('field'); original = item.get('text')
        if field not in FIELDS or not isinstance(original, str) or not original.strip() or not item.get('source_location'):
            raise ValueError(f'{sid}: 源字段、原文或定位缺失')
        d = by_item[sid]; status = d.get('status')
        if status not in ('included', 'modified', 'omitted', 'not_applicable') or not str(d.get('reason', '')).strip():
            raise ValueError(f'{sid}: 处置状态或理由缺失')
        if status in ('modified', 'omitted') and not str(d.get('user_authorization', '')).strip():
            raise ValueError(f'{sid}: 改写或删减缺少用户授权依据')
        if status == 'not_applicable' and field in ('dialogue', 'action'):
            raise ValueError(f'{sid}: 有源对白或动作不能以不适用代替用户授权删减')
        evidence = d.get('evidence', [])
        if status in ('omitted', 'not_applicable'):
            if evidence:
                raise ValueError(f'{sid}: 不适用或删减不能附交付证据')
            continue
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f'{sid}: 缺少成品正文证据')
        positions = []
        for entry in evidence:
            cid = entry.get('clip_id'); quote = entry.get('excerpt'); window = entry.get('time_window')
            if cid not in by_clip or not isinstance(quote, str) or not quote.strip() or quote not in by_clip[cid]['prompt'] or not isinstance(window, str) or not window.strip():
                raise ValueError(f'{sid}: 成品正文、段号或时间窗证据无效')
            actors = entry.get('actors', [])
            if not isinstance(actors, list) or not set(actors).issubset(set(by_clip[cid]['visible_cast'])):
                raise ValueError(f'{sid}: 表演或反应对象不在画')
            if field in ('performance', 'reaction') and not actors:
                raise ValueError(f'{sid}: 表演或反应缺少在画对象')
            positions.append(order[cid])
        if positions != sorted(positions):
            raise ValueError(f'{sid}: 跨段证据顺序错误')
        if field == 'dialogue' and status == 'included':
            # Contiguous split fragments must reconstruct the exact source dialogue.
            if ''.join(e['excerpt'] for e in evidence) != original:
                raise ValueError(f'{sid}: 对白未逐字覆盖原文')
    return {'status': 'passed', 'source_items': len(items), 'clips': len(clips)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--delivery', required=True)
    args = parser.parse_args()
    try:
        result = validate(json.loads(Path(args.source).read_text(encoding='utf-8')), json.loads(Path(args.delivery).read_text(encoding='utf-8')))
    except (ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'交付检查失败: {exc}\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
