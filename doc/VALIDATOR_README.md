# JSON-LD to RDF Ontology Validator

## 概要

`jsonld_validator.py`は、JSON-LDインスタンスデータがRDF/Turtleオントロジー定義に準拠しているかを検証するツールです。

このバリデータは`doc/RDF_JSON_LD_MAPPING.md`で定義された対応ルールに基づいて、以下を検証します：

- ✅ 命名規則（camelCase → snake_case）
- ✅ データ型（XSD → JSON型）
- ✅ 構造の正確性（ネスト、配列）
- ✅ クラスとプロパティの存在
- ✅ @contextと@typeの妥当性

---

## インストール

### 必要なパッケージ

```bash
pip install rdflib
```

### ファイル

- `jsonld_validator.py` - メインバリデータ
- `doc/RDF_JSON_LD_MAPPING.md` - 対応ルールのドキュメント

---

## 使用方法

### 基本的な使い方

```bash
python jsonld_validator.py <ontology.ttl> <data.json> [report.txt]
```

**パラメータ:**
- `ontology.ttl` - RDF/Turtleオントロジーファイル
- `data.json` - 検証するJSON-LDファイル
- `report.txt` - （オプション）レポート出力ファイル

### 例

```bash
# 製造データの検証
python jsonld_validator.py \
    model/source/manufacturing-ontology.ttl \
    test_data/source/sample1_small_factory.json \
    validation_report.txt
```

```bash
# GHGレポートデータの検証
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/correct_output.json
```

### Pythonコードから使用

```python
from jsonld_validator import OntologyValidator, generate_validation_report

# バリデータの作成
validator = OntologyValidator('model/source/manufacturing-ontology.ttl')

# 検証実行
result = validator.validate('test_data/source/sample1_small_factory.json')

# 結果確認
print(f"Valid: {result.valid}")
print(f"Errors: {len([i for i in result.issues if i.severity == 'error'])}")
print(f"Warnings: {len([i for i in result.issues if i.severity == 'warning'])}")

# レポート生成
report = generate_validation_report(result)
print(report)

# ファイルに保存
generate_validation_report(result, 'validation_report.txt')
```

---

## 検証項目

### 1. 命名規則の検証

**チェック内容:**
- フィールド名が`snake_case`か
- 配列フィールドが複数形か

**例:**

```json
// ❌ エラー
{
  "activityId": "ACT-001",           // camelCase
  "energy_consumption": [...]        // 単数形
}

// ✅ 正しい
{
  "activity_id": "ACT-001",          // snake_case
  "energy_consumptions": [...]       // 複数形
}
```

**出力:**
```
⚠️  WARNING
Path: $.activityId
Category: naming
Message: Field name should be snake_case
Expected: activity_id
Actual: activityId
```

### 2. クラスの検証

**チェック内容:**
- `@type`で指定されたクラスがオントロジーに存在するか

**例:**

```json
// ❌ エラー
{
  "@type": "mfg:InvalidClass"  // 存在しないクラス
}

// ✅ 正しい
{
  "@type": "mfg:ManufacturingActivity"  // オントロジーに定義されている
}
```

**出力:**
```
❌ ERROR
Path: $.@type
Category: type
Message: Class "InvalidClass" not found in ontology
Actual: InvalidClass
Suggestion: Available classes: ManufacturingActivity, Product, ...
```

### 3. データ型の検証

**チェック内容:**
- フィールドの値の型がオントロジーで定義された`rdfs:range`と一致するか

**XSD → JSON型のマッピング:**
| XSD型 | JSON型 |
|-------|--------|
| `xsd:string` | string |
| `xsd:decimal` | number |
| `xsd:integer` | number |
| `xsd:boolean` | boolean |
| `xsd:date` | string (ISO 8601) |

**例:**

```json
// ❌ エラー
{
  "quantity": "5000"  // 文字列だが数値であるべき
}

// ✅ 正しい
{
  "quantity": 5000    // 数値
}
```

**出力:**
```
❌ ERROR
Path: $.quantity
Category: type
Message: Type mismatch
Expected: int
Actual: str
```

### 4. プロパティの検証

**チェック内容:**
- フィールドがオントロジーに定義されたプロパティと対応しているか
- 未定義のプロパティに対して類似の候補を提案

**例:**

```json
{
  "activity_id": "ACT-001"  // オントロジーの mfg:activityId に対応
}
```

**出力（未定義プロパティの場合）:**
```
⚠️  WARNING
Path: $.unknown_field
Category: unknown
Message: Property not found in ontology
Actual: unknown_field
Suggestion: Did you mean: activity_id, activity_name?
```

### 5. 構造の検証

**チェック内容:**
- ObjectPropertyがオブジェクトまたは配列か
- ネストされた構造が適切か

---

## 検証レポート

### レポート形式

```
======================================================================
JSON-LD VALIDATION REPORT
======================================================================

Status: ❌ INVALID
Errors: 2
Warnings: 3
Info: 1

❌ ERRORS
----------------------------------------------------------------------
Path: $.@type
Category: type
Message: Class "InvalidClass" not found in ontology
Actual: InvalidClass
Suggestion: Available classes: ManufacturingActivity, Product, ...

⚠️  WARNINGS
----------------------------------------------------------------------
Path: $.activityId
Category: naming
Message: Field name should be snake_case
Expected: activity_id
Actual: activityId

ℹ️  INFORMATION
----------------------------------------------------------------------
Path: $.extra_field
Message: Property "extra_field" not defined in ontology (may be valid)

======================================================================
```

### 重大度レベル

1. **ERROR (❌)**: 重大な問題。データがオントロジーに違反している
   - 存在しないクラス
   - 型の不一致

2. **WARNING (⚠️)**: 警告。推奨されない使い方
   - 命名規則違反（camelCase）
   - 未定義のプロパティ

3. **INFO (ℹ️)**: 情報。問題ではないが注意が必要
   - オントロジーに定義されていないが有効な可能性があるフィールド

### 終了コード

- `0` - 検証成功（エラーなし）
- `1` - 検証失敗（エラーあり）

---

## 実行例

### 例1: 正しいデータの検証

**コマンド:**
```bash
python jsonld_validator.py \
    model/source/manufacturing-ontology.ttl \
    test_data/source/sample1_small_factory.json
```

**出力:**
```
Validating: test_data/source/sample1_small_factory.json
Against ontology: model/source/manufacturing-ontology.ttl

======================================================================
JSON-LD VALIDATION REPORT
======================================================================

Status: ✅ VALID
Errors: 0
Warnings: 4
Info: 2

⚠️  WARNINGS
----------------------------------------------------------------------
Path: $.organization.name
Category: unknown
Message: Property not found in ontology
Actual: name
Suggestion: Did you mean: activity_name, product_name?

...

======================================================================
```

### 例2: エラーを含むデータの検証

**コマンド:**
```bash
python jsonld_validator.py \
    model/source/manufacturing-ontology.ttl \
    test_data/invalid_sample.json
```

**出力:**
```
Validating: test_data/invalid_sample.json
Against ontology: model/source/manufacturing-ontology.ttl

======================================================================
JSON-LD VALIDATION REPORT
======================================================================

Status: ❌ INVALID
Errors: 2
Warnings: 4
Info: 0

❌ ERRORS
----------------------------------------------------------------------
Path: $.manufacturingActivities[0].@type
Category: type
Message: Class "InvalidClass" not found in ontology
Actual: InvalidClass

Path: $.manufacturingActivities[0].produces.quantity
Category: type
Message: Type mismatch
Expected: int
Actual: str

⚠️  WARNINGS
----------------------------------------------------------------------
Path: $.manufacturingActivities
Category: naming
Message: Field name should be snake_case
Expected: manufacturing_activities
Actual: manufacturingActivities

...

======================================================================
```

---

## 高度な使用方法

### カスタム検証ルールの追加

```python
from jsonld_validator import OntologyValidator, ValidationResult

class CustomValidator(OntologyValidator):
    def validate(self, json_file: str, strict: bool = False) -> ValidationResult:
        result = super().validate(json_file, strict)

        # カスタム検証ロジック
        # ...

        return result
```

### 特定の検証項目のみ実行

```python
validator = OntologyValidator('ontology.ttl')

with open('data.json', 'r') as f:
    data = json.load(f)

result = ValidationResult(valid=True)

# 命名規則のみチェック
validator._validate_naming('activityId', result, '$.activityId')

print(result.issues)
```

---

## よくある質問

### Q1: Warningが出ますが、データは正しいです

**A:** Warningは推奨事項です。以下のような場合に出ます：

1. **未定義プロパティ**: `organization.name`など、オントロジーに定義されていないが実際には有効なフィールド
2. **短縮化されたフィールド名**: `name`（ネスト内）は`energyTypeName`の短縮形

これらは実用上問題ありませんが、オントロジーと完全に一致していないため警告されます。

### Q2: snake_caseエラーを無視したい

**A:** 現在のバリデータはsnake_caseを強制しますが、以下のように回避できます：

1. データをsnake_caseに修正（推奨）
2. バリデータのコードを修正して警告を抑制

### Q3: オントロジーに定義されていないフィールドは使えないの？

**A:** JSON-LD仕様では、オントロジーに定義されていないフィールドも許容されます。バリデータは**warning**として報告しますが、エラーではありません。

### Q4: カスタムオントロジーで使用できますか？

**A:** はい、任意のOWL/RDFSオントロジーに対応しています：

```bash
python jsonld_validator.py your_ontology.ttl your_data.json
```

---

## 制限事項

1. **複雑な制約**: OWL制約（cardinality、disjointなど）は現在サポートされていません
2. **推論**: RDFSの推論は限定的です
3. **カスタム型**: カスタムXSD型は基本型として扱われます
4. **ネストした短縮化**: 深くネストされたフィールドの短縮化検出は限定的

---

## トラブルシューティング

### エラー: "Failed to load JSON file"

**原因:** JSON形式が不正

**解決策:**
```bash
# JSONの文法チェック
python -m json.tool data.json
```

### エラー: "Failed to parse ontology"

**原因:** RDF/Turtle形式が不正

**解決策:**
```bash
# RDFLibでパース確認
python -c "from rdflib import Graph; g = Graph(); g.parse('ontology.ttl', format='turtle')"
```

### 警告が多すぎる

**解決策:** レポートをファイルに出力して確認

```bash
python jsonld_validator.py ontology.ttl data.json report.txt
grep "ERROR" report.txt  # エラーのみ表示
```

---

## 関連ドキュメント

- **`doc/RDF_JSON_LD_MAPPING.md`** - RDFとJSON-LDの対応ルール詳細
- **`AI_RULE_ANALYSIS.md`** - AI生成ルールの問題分析
- **`transformation_rules.yaml`** - 正しい変換ルールの例

---

## テストケース

### 正しいデータ

- `test_data/source/sample1_small_factory.json`
- `test_data/source/sample2_multi_fuel.json`
- `test_data/source/sample3_electronics.json`
- `output/correct_output.json`

### エラーを含むデータ

- `test_data/invalid_sample.json` - 意図的にエラーを含むサンプル
- `output/ai_output_small_factory.json` - AI生成ルールの失敗例

---

## まとめ

このバリデータは以下の用途に最適です：

1. ✅ **データ作成時の検証** - 新規JSON-LDデータがオントロジーに準拠しているか確認
2. ✅ **既存データの監査** - 既存データの品質確認
3. ✅ **CI/CD統合** - 自動テストパイプラインに組み込み
4. ✅ **開発者支援** - 命名規則やデータ型の間違いを早期発見
5. ✅ **AI生成データの検証** - AI生成されたデータの正確性確認

**次のステップ:**
- データがエラーを含む場合、`doc/RDF_JSON_LD_MAPPING.md`を参照して修正
- 変換ルール作成時は、検証済みのデータを基に設計

---

**作成日:** 2025-11-12
**バージョン:** 1.0
