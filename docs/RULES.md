# 门店置换规则说明

## 1. 当前规则来源

当前应用实际使用的门店规则模板保存在 SQLite 的 `exchange_rules` 表中，通过 `/api/rules` 管理。

`rules/brands/*.json` 是项目早期的品牌费用规则和示例文件，目前不负责计算页的门店置换模板，也不会覆盖数据库中用户编辑的规则。后续如继续保留，应把它们视为参考资料或导入来源。

## 2. 规则字段

```json
{
  "name": "周大福南京东路店",
  "brand": "chow_tai_fook",
  "city": "上海",
  "store_name": "南京东路店",
  "support_bar": true,
  "support_other_brand": true,
  "support_old_jewelry": true,
  "need_extra_gold": true,
  "extra_rate": 20,
  "loss_type": "percentage",
  "loss_value": 0.2,
  "labor_type": "perGram",
  "labor_value": 30,
  "recycle_price_type": "recycle"
}
```

| 字段 | 说明 |
| --- | --- |
| `name` | 模板名称 |
| `brand` | 新金品牌 ID |
| `city` | 城市，可为空 |
| `store_name` | 门店或商场名称，可为空 |
| `support_bar` | 是否接受金条置换 |
| `support_other_brand` | 是否接受非本品牌旧金 |
| `support_old_jewelry` | 是否接受旧饰品 |
| `need_extra_gold` | 是否要求新金比旧金更重 |
| `extra_rate` | 最低增金百分比 |
| `loss_type` | 当前固定为 `percentage` |
| `loss_value` | 旧金每克损耗百分比，范围 0～100 |
| `labor_type` | `fixed` 固定工费，或 `perGram` 按克收费 |
| `labor_value` | 工费数值 |
| `recycle_price_type` | `recycle` 按回收价，或 `jewelry` 按饰品价 |

按产品要求，当前不记录生效日期和信息来源。

## 3. 校验规则

### 3.1 增金

勾选“要求增金”时，`extra_rate` 必须大于 0；未勾选时系统保存为 0。

```text
最低新金重量 = 旧金重量 × (1 + extra_rate ÷ 100)
```

新金重量不足时，前端禁用计算并提示，后端也会返回 `400`，避免绕过页面校验。

### 3.2 损耗

损耗不再支持“固定克数”模式，统一按旧金重量的百分比计算：

```text
损耗重量 = 旧金重量 × loss_value ÷ 100
可抵扣重量 = 旧金重量 - 损耗重量
```

“每克损耗 2%”表示每克只保留 98%，10g 旧金最终损耗 0.2g。

### 3.3 适用范围

- 旧金为金条且 `support_bar=false`：拒绝计算。
- 旧、新金品牌不同且 `support_other_brand=false`：拒绝计算。
- 旧金为饰品且 `support_old_jewelry=false`：拒绝计算。
- 未使用旧金时，不执行以上置换适用性校验。

### 3.4 工费和回收计价

计算页会填写当前饰品实际工费，该值优先于模板工费，因此同一品牌不同饰品可以使用不同工费。

直接调用 API 且未提供 `purchase.labor_fee` 时：

- `fixed`：使用 `labor_value` 作为工费总额。
- `perGram`：使用 `labor_value × 新金重量`。

回收计价：

- `jewelry`：按新金单价计算旧金抵扣。
- `recycle`：优先使用请求中的实际回收价；未提供时暂按新金单价的 85% 估算。

## 4. 页面行为

### 规则页

- 负责规则模板的新增、编辑和删除。
- 只有勾选“要求增金”时才显示增金比例输入。
- 规则卡片展示品牌、城市、门店或商场、增金、损耗、工费和适用标签。

### 计算页

- 选择模板后展示完整的只读详情。
- 详情区域没有输入框，不能直接修改模板。
- “去规则管理修改”跳转到规则页。
- “自定义规则”是当前方案的一次性规则，不会修改所选模板。

## 5. 默认种子模板

首次创建空数据库时写入：

- 周大福默认规则。
- 周生生默认规则。
- 老凤祥默认规则。

种子只在规则表为空时创建，不会覆盖已有模板。

## 6. 后续方向

当前模板是整个应用共享的数据。后续用户系统上线后，应给规则增加用户归属，实现：

- 用户只能编辑自己的规则。
- 用户可复制系统示例为个人模板。
- 分享方案时明确规则快照，避免模板后续修改导致结果变化。
- 可选的规则导入、导出和版本记录。
