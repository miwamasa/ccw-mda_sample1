# MDA-based Data Transformation: Manufacturing to GHG Emission Report

MDA（Model-Driven Architecture）原則に基づいた、製造データからGHG（温室効果ガス）排出レポートへの自動変換システム。

## 📋 概要

このプロジェクトは、製造活動データ（JSON-LD）をGHG排出レポート（JSON-LD）に変換します：

- **Source Model**: 製造オントロジー（manufacturing-ontology.ttl）
- **Target Model**: GHG報告オントロジー（ghg-report-ontology.ttl）
- **Transformation**: 宣言的なYAMLルールベース

### 主要な機能

✅ **自動データ変換** - 製造活動データ → GHG排出レポート
✅ **排出量計算** - エネルギー消費量 × 排出係数 = CO2排出量
✅ **Scope分類** - Scope 1（直接排出）/ Scope 2（間接排出）の自動判定
✅ **集計** - 活動別、Scope別、総排出量の計算
✅ **AI生成ルール** - Claude AIによる変換ルールの自動生成
✅ **データ検証** - JSON-LDデータのオントロジー準拠性検証

## 🚀 クイックスタート

### 1. データ変換（手作りルール使用）

```bash
# 製造データをGHG排出レポートに変換
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/ghg_report.json

# 結果: Total emissions: 12,175.5 kg-CO2
```

### 2. AI生成ルールで変換

```bash
# APIキーを設定
export ANTHROPIC_API_KEY='your-key-here'

# AIでルール生成
python ai_rule_generator.py --no-verify-ssl \
    model/source/manufacturing-ontology.ttl \
    model/target/ghg-report-ontology.ttl \
    output/ai_rules.yaml

# 生成されたルールで変換
python rule_engine.py \
    output/ai_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/ai_ghg_report.json
```

### 3. データ検証

```bash
# 出力データをオントロジーに対して検証
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ghg_report.json
```

## 📁 プロジェクト構造

```
ccw-mda_sample1/
├── README.md                          # このファイル
├── doc/                               # ドキュメント
│   ├── AI_RULE_GENERATOR.md          # AI生成の完全ガイド
│   ├── TESTING.md                     # テスト手順
│   ├── TROUBLESHOOTING.md            # トラブルシューティング
│   ├── TEST_RESULTS.md               # テスト結果詳細
│   ├── RDF_JSON_LD_MAPPING.md        # RDF↔JSON-LDマッピング
│   └── VALIDATOR_README.md           # Validator使用方法
│
├── model/                             # オントロジー定義
│   ├── source/manufacturing-ontology.ttl
│   └── target/ghg-report-ontology.ttl
│
├── test_data/                         # テストデータ
│   ├── source/                        # 入力データ
│   │   ├── sample1_small_factory.json
│   │   ├── sample2_multi_fuel.json
│   │   └── sample3_electronics.json
│   └── target/                        # 期待される出力
│
├── output/                            # 変換結果
│   ├── correct_output.json           # 手作りルールの正解
│   ├── ai_generated_rules_v2_improved.yaml
│   └── ai_output_v2_improved.json    # AI生成（改善版）
│
├── transformation_rules.yaml          # 手作りの変換ルール（正解）
├── transformer.py                     # 初期実装（ハードコード）
├── rule_engine.py                    # ルールベース変換エンジン
├── rule_generator.py                 # 自動ルール生成
├── ai_rule_generator.py              # AI生成（改善版）
└── jsonld_validator.py               # JSON-LD検証ツール
```

## 🔧 主要コンポーネント

### 1. Rule Engine (`rule_engine.py`)

YAMLルールに基づいてデータ変換を実行：

```yaml
transformation_steps:
  - name: transform_activities_to_emissions
    source: manufacturing_activities
    target: emissions
    iteration: true
    substeps:
      - name: iterate_energy_consumptions
        source: $.energy_consumptions
        iteration: true
        mapping:
          - target: co2_amount
            calculation: calculate_co2_emission
          - target: source_category
            source: $.energy_type.name
```

**機能:**
- フィールドマッピング
- 計算ルール実行
- 集計（sum, count, average）
- ルックアップテーブル
- 条件付きマッピング

### 2. AI Rule Generator (`ai_rule_generator.py`)

Claude AIで変換ルールを自動生成：

**特徴:**
- ✅ オントロジーを分析してマッピングを提案
- ✅ 自動substeps生成（AI提案 + フォールバック）
- ✅ 必須calculation_rulesを自動追加
- ✅ 正しいemission factorsを自動設定
- ✅ rule_engine互換の構造を保証

**使用方法:** → [doc/AI_RULE_GENERATOR.md](doc/AI_RULE_GENERATOR.md)

### 3. JSON-LD Validator (`jsonld_validator.py`)

JSON-LDデータをオントロジーに対して検証：

**検証項目:**
- ✅ フィールド命名規則（snake_case）
- ✅ クラスの存在確認
- ✅ プロパティの型チェック
- ✅ 必須フィールドの確認

**使用方法:** → [doc/VALIDATOR_README.md](doc/VALIDATOR_README.md)

## 📊 変換例

### 入力（Manufacturing Activity）

```json
{
  "manufacturing_activities": [
    {
      "@type": "mfg:ManufacturingActivity",
      "activity_id": "ACT-2024-001",
      "activity_name": "Widget Assembly Line A",
      "facility": "Factory Tokyo Plant 1",
      "energy_consumptions": [
        {
          "@type": "mfg:EnergyConsumption",
          "energy_type": {
            "@type": "mfg:EnergyType",
            "name": "electricity"
          },
          "amount": 12500,
          "unit": "kWh"
        }
      ]
    }
  ]
}
```

### 出力（GHG Emission Report）

```json
{
  "@type": "ghg:EmissionReport",
  "report_id": "GHG-AML-2024-01",
  "reporting_period": "2024-01",
  "reporting_organization": {
    "organization_name": "Acme Manufacturing Ltd"
  },
  "emissions": [
    {
      "@type": "ghg:Scope2Emission",
      "emission_source": "Factory Tokyo Plant 1 - Widget Assembly Line A",
      "source_category": "electricity",
      "co2_amount": 6250.0,
      "emission_factor": 0.5,
      "calculation_method": "Activity-based calculation..."
    }
  ],
  "total_emissions": 12175.5,
  "total_scope1": 1725.5,
  "total_scope2": 10450.0
}
```

**変換内容:**
- ✅ 12,500 kWh × 0.5 kg-CO2/kWh = 6,250 kg-CO2
- ✅ electricity → Scope 2 Emission
- ✅ 3活動の排出量を集計 → total: 12,175.5 kg-CO2

## 🧪 テスト

### 自動テスト

```bash
# AI生成の完全テスト（APIキー必要）
./test_ai_generator.sh

# 個別テスト
python test_improved_rule_generation.py  # 自動生成ロジックのテスト
python test_rule_engine.py              # Rule engineのテスト
```

### 手動テスト

詳細は [doc/TESTING.md](doc/TESTING.md) を参照。

## 📚 ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [AI_RULE_GENERATOR.md](doc/AI_RULE_GENERATOR.md) | AI生成の完全ガイド |
| [TESTING.md](doc/TESTING.md) | テスト手順 |
| [TROUBLESHOOTING.md](doc/TROUBLESHOOTING.md) | 問題解決ガイド |
| [TEST_RESULTS.md](doc/TEST_RESULTS.md) | テスト結果詳細 |
| [RDF_JSON_LD_MAPPING.md](doc/RDF_JSON_LD_MAPPING.md) | オントロジー↔データマッピング |
| [VALIDATOR_README.md](doc/VALIDATOR_README.md) | Validator使用方法 |

## 🔑 主要な技術成果

### 1. AI生成ルールの改善

**課題:** AIが生成するルールのsubstepsが空で、出力が0 kg-CO2

**解決策:**
- 改善されたプロンプト（JSON-LD命名規則の詳細説明）
- 自動substeps生成ロジック（AIフォールバック）
- 必須calculation_rulesの自動追加

**結果:** 0 → **12,175.5 kg-CO2** ✅

詳細: [doc/TROUBLESHOOTING.md](doc/TROUBLESHOOTING.md)

### 2. RDF-JSON-LDマッピングの文書化

**成果:** オントロジー（camelCase）とJSON-LD（snake_case）の完全な対応表

| Ontology | JSON-LD | 変換ルール |
|----------|---------|-----------|
| `hasEnergyConsumption` | `energy_consumptions` | snake_case + 複数形 |
| `activityName` | `activity_name` | snake_case |
| `energyTypeName` | `name` | ネスト内で簡略化 |

詳細: [doc/RDF_JSON_LD_MAPPING.md](doc/RDF_JSON_LD_MAPPING.md)

### 3. JSON-LD検証ツール

**機能:**
- オントロジー準拠性の自動検証
- 型チェック（XSD → JSON）
- 命名規則チェック
- 詳細なエラーレポート

詳細: [doc/VALIDATOR_README.md](doc/VALIDATOR_README.md)

## 🛠️ 開発の進化

### Phase 1: ハードコード実装
```python
# transformer.py - 初期実装
def transform(source):
    return {
        "total_emissions": calculate_emissions(source)
    }
```

### Phase 2: YAMLルールベース
```yaml
# transformation_rules.yaml
field_mappings:
  - source_path: activity_name
    target_path: emission_source
```

### Phase 3: 自動ルール生成
```python
# rule_generator.py
rules = OntologyAnalyzer.generate_rules(source_ont, target_ont)
```

### Phase 4: AI生成（改善版）
```python
# ai_rule_generator.py + 自動補完
rules = AIRuleGenerator.generate_rules()  # AI提案
rules = auto_generate_substeps(rules)     # 互換性保証
```

## 🎯 使用例

### 例1: 小規模工場

```bash
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/small_factory_report.json

# 結果: 2活動、3エネルギー消費、12,175.5 kg-CO2
```

### 例2: 複数燃料使用

```bash
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample2_multi_fuel.json \
    output/multi_fuel_report.json

# 結果: Scope 1 + Scope 2混在
```

### 例3: カスタムルール生成

```bash
# 新しいオントロジーペア用のルール生成
python ai_rule_generator.py \
    model/source/custom-source.ttl \
    model/target/custom-target.ttl \
    output/custom_rules.yaml
```

## ⚙️ 設定

### 排出係数（transformation_rules.yaml）

```yaml
constants:
  emission_factors:
    electricity: 0.500   # kg-CO2/kWh
    natural_gas: 2.03    # kg-CO2/m³
    diesel: 2.68         # kg-CO2/liter
    gasoline: 2.31       # kg-CO2/liter
    fuel_oil: 2.68       # kg-CO2/liter
```

### Scope分類

```yaml
constants:
  scope_classification:
    scope1:  # 直接排出
      - natural_gas
      - diesel
      - gasoline
      - fuel_oil
    scope2:  # 間接排出（購入エネルギー）
      - electricity
```

## 🔍 トラブルシューティング

### Q: AIが空のsubstepsを生成する

**A:** 自動生成ロジックが対応済み。詳細は [doc/TROUBLESHOOTING.md](doc/TROUBLESHOOTING.md#empty-substeps)

### Q: 変換結果が0 kg-CO2

**A:** ルールファイルを確認。[doc/TROUBLESHOOTING.md](doc/TROUBLESHOOTING.md#zero-emissions)

### Q: SSL証明書エラー

**A:** `--no-verify-ssl` フラグを使用。詳細は [doc/AI_RULE_GENERATOR.md](doc/AI_RULE_GENERATOR.md#ssl-issues)

## 📈 パフォーマンス

| テストケース | 入力サイズ | 処理時間 | 出力 |
|-------------|----------|---------|------|
| sample1_small_factory | 2活動 | <0.1秒 | 12,175.5 kg-CO2 |
| sample2_multi_fuel | 3活動 | <0.1秒 | 正常 |
| sample3_electronics | 5活動 | <0.2秒 | 正常 |

## 🤝 貢献

このプロジェクトはMDA原則とJSON-LD技術の実証実験です。

## 📄 ライセンス

研究・教育目的のサンプルプロジェクト

## 🔗 関連リソース

- **RDF/OWL**: https://www.w3.org/TR/owl2-overview/
- **JSON-LD**: https://json-ld.org/
- **GHG Protocol**: https://ghgprotocol.org/
- **MDA**: https://www.omg.org/mda/

---

**作成日:** 2024-01-01
**最終更新:** 2025-11-12
**ステータス:** ✅ 動作確認済み
**Total Emissions:** 12,175.5 kg-CO2 （サンプルデータ）
