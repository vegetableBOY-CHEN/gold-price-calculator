# 品牌规则说明 (RULES)

## 规则文件位置

```
rules/brands/{brand_id}.json
```

## JSON Schema

```json
{
  "id": "string",           // 品牌唯一标识（文件名一致）
  "name": "string",         // 中文名
  "name_en": "string",      // 英文名（可选）
  "description": "string",  // 描述（可选）
  "gold_price_source": "manual | api",
  "labor_fee": { ... },     // 工费规则（可选）
  "craft_fee": { ... },     // 工艺费规则（可选）
  "other_fees": [ ... ],    // 其他费用列表
  "notes": "string"         // 备注（可选）
}
```

## 费用类型 (FeeRule)

| type | 说明 | value 含义 |
|------|------|-----------|
| `fixed` | 固定金额 | 元 |
| `per_gram` | 按克计费 | 元/克 |
| `percentage` | 按材料费百分比 | 百分比数值（如 5 表示 5%） |

## 计算公式

```
有效重量 = 重量 × 成色
材料费 = 有效重量 × 当日金价
各项费用 = 按 FeeRule 类型计算
总价 = 材料费 + 所有费用 + 额外费用
```

## 添加新品牌

1. 在 `rules/brands/` 创建 `{brand_id}.json`
2. 按 Schema 填写规则
3. 在 `rules/examples/` 添加计算示例（可选）
4. 重启后端或等待缓存刷新

## 示例

参见 `rules/examples/chow_tai_fook_10g.json`
