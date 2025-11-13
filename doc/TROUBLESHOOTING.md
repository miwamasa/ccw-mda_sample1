# トラブルシューティングガイド

このドキュメントでは、MDA-based Data Transformation システムで発生する一般的な問題と解決方法を説明します。

## 📋 目次

1. [AI Rule Generator の問題](#ai-rule-generator-の問題)
2. [データ変換の問題](#データ変換の問題)
3. [Validator の問題](#validator-の問題)
4. [ネットワークとAPI の問題](#ネットワークとapi-の問題)
5. [データ構造の問題](#データ構造の問題)

---

## 🤖 AI Rule Generator の問題

### ❌ 問題: 空のsubsteps

<a name="empty-substeps"></a>

**症状:**
```yaml
transformation_steps:
  - name: transform_activities
    source: manufacturing_activities
    target: emissions
    iteration: true
    substeps: []  # ❌ 空！
```

**影響:** 変換結果が空（total_emissions = 0）

**原因:**
- AIがsubstepsを生成していない
- または、AIが非互換の構造を生成した（`field_mappings` vs `mapping`）

**解決方法:**

1. **最新版のai_rule_generator.pyを使用**
   ```bash
   # 最新版は自動生成ロジックを含む
   git pull origin main
   ```

2. **自動生成ロジックの確認**
   ```bash
   # テストを実行して自動生成が動作していることを確認
   python test_improved_rule_generation.py

   # 期待される出力:
   # ✅ Substeps generated: 1-2 items
   # ✅ Calculation rules: 2 items
   # ✅ Constants: emission_factors present
   ```

3. **生成されたルールを確認**
   ```bash
   # substepsが空でないことを確認
   grep -A 10 "substeps:" output/ai_generated_rules.yaml

   # mappingキーが存在することを確認（field_mappingsではない）
   grep "mapping:" output/ai_generated_rules.yaml
   ```

**自動生成ロジックの仕組み:**

```python
# ai_rule_generator.py の動作
ai_substeps = step_info.get('substeps', [])
if ai_substeps:
    # AIが提案した場合、使用を試みる
    step['substeps'] = ai_substeps
else:
    # AIが提供しない場合、自動生成
    step['substeps'] = self._auto_generate_substeps(step, suggestions)
```

---

### ❌ 問題: 変換結果が0 kg-CO2

<a name="zero-emissions"></a>

**症状:**
```json
{
  "emissions": [],
  "total_emissions": 0
}
```

または

```json
{
  "emissions": [{}, {}, {}],  // 空のオブジェクト
  "total_emissions": 0
}
```

**原因と解決方法:**

#### 原因1: substepsが空

**確認:**
```bash
grep -A 5 "substeps:" output/ai_generated_rules.yaml
```

**解決:** [空のsubsteps](#empty-substeps) を参照

#### 原因2: 計算ルールが実行されない

**確認:**
```bash
# calculation_rulesに calculate_co2_emission があるか確認
grep "calculate_co2_emission" output/ai_generated_rules.yaml

# transformation_stepsでcalculationが参照されているか確認
grep "calculation: calculate_co2_emission" output/ai_generated_rules.yaml
```

**解決:**

最新版のai_rule_generator.pyは自動的に必須calculation_rulesを追加します：

```yaml
calculation_rules:
  - name: calculate_co2_emission
    input:
      energy_amount: $.amount
      energy_type: $.energy_type.name
    formula: energy_amount * emission_factor
    lookup:
      emission_factor:
        source: constants.emission_factors
        key: energy_type
        key_transform: lowercase_underscore
    output: co2_amount
    rounding: 2
```

#### 原因3: emission_factorsが不正確または存在しない

**確認:**
```bash
grep -A 5 "emission_factors:" output/ai_generated_rules.yaml
```

**期待される値:**
```yaml
constants:
  emission_factors:
    electricity: 0.5      # kg-CO2/kWh
    natural_gas: 2.03     # kg-CO2/m³
    diesel: 2.68          # kg-CO2/liter
    gasoline: 2.31        # kg-CO2/liter
    fuel_oil: 2.68        # kg-CO2/liter
```

**解決:**

最新版のai_rule_generator.pyは自動的に正しいemission_factorsを追加します。

#### 原因4: aggregation sourceが間違っている

**確認:**
```bash
grep -A 5 "aggregations:" output/ai_generated_rules.yaml
```

**間違った例:**
```yaml
aggregations:
  - name: total_emissions
    source: s  # ❌ 間違い！
```

**正しい例:**
```yaml
aggregations:
  - name: total_emissions
    source: emissions  # ✅ 正しい
    aggregate:
      function: sum
      field: co2_amount
```

**解決:**

最新版のai_rule_generator.pyは自動的に正しいsourceを設定します。

---

### ❌ 問題: AIが非互換の構造を生成

**症状:**

AI生成のYAMLファイルが以下のような構造を持つ：

```yaml
transformation_steps:
  - name: transform_activities
    substeps:
      - name: iterate_energy
        substeps:  # ❌ 2レベルのネスト
          - name: map_fields
            field_mappings:  # ❌ 非互換のキー名
              - target: co2_amount
                source: $.amount
```

**原因:** AIが高度な構造を生成したが、rule_engineが対応していない

**解決方法:**

自動生成ロジックがフォールバックとして動作し、rule_engine互換の構造を生成します：

```yaml
transformation_steps:
  - name: transform_activities_to_emissions
    substeps:
      - name: iterate_energy_consumptions
        source: $.energy_consumptions
        iteration: true
        mapping:  # ✅ 互換性のあるキー名
          - target: co2_amount
            calculation: calculate_co2_emission
```

**確認:**
```bash
python test_improved_rule_generation.py
# ✅ 期待: Total emissions = 12175.5
```

---

## 🔄 データ変換の問題

### ❌ 問題: フィールドが"Unknown"になる

**症状:**
```json
{
  "emission_source": "Unknown",
  "source_category": "Unknown"
}
```

**原因:** フィールドマッピングが正しくない

**診断:**
```bash
# ルールファイルのfield_mappingsを確認
grep -A 10 "field_mappings:" transformation_rules.yaml
```

**一般的な間違い:**

1. **配列内のフィールドをルートレベルでマッピング**
   ```yaml
   # ❌ 間違い
   field_mappings:
     - source_path: activity_name  # これは配列内にある
       target_path: emission_source
   ```

2. **正しいパス指定**
   ```yaml
   # ✅ 正しい（transformation_stepsで処理）
   transformation_steps:
     - name: transform_activities
       source: manufacturing_activities
       iteration: true
       substeps:
         - name: process_energy
           mapping:
             - target: emission_source
               source: $.activity_name
   ```

**解決方法:**

1. 手作りの `transformation_rules.yaml` を参考にする
2. transformation_stepsとsubstepsを正しく使用する

---

### ❌ 問題: null値が含まれる

**症状:**
```json
{
  "emission_source": null,
  "source_category": null,
  "co2_amount": 6250.0  // これは正しい
}
```

**原因:** rule_engineが `context: parent` をサポートしていない

**診断:**
```bash
grep "context: parent" output/ai_generated_rules.yaml
```

**影響:**
- 主要な計算（co2_amount、total_emissions）は正しい
- 一部のメタデータフィールド（emission_source、source_category）がnull

**解決方法:**

これはrule_engine.pyの制限です。以下のいずれかを選択：

1. **Option A:** 主要な指標が正しければ許容する
   - total_emissions = 12,175.5 kg-CO2 が正しい ✅
   - nullフィールドは表示上の問題のみ

2. **Option B:** rule_engine.pyを拡張してparent contextをサポート
   ```python
   # rule_engine.py に機能追加が必要
   if mapping.get('context') == 'parent':
       # 親オブジェクトから値を取得
       value = parent_data.get(source_field)
   ```

3. **Option C:** ルールを調整して別の方法でマッピング
   ```yaml
   # parent contextを使わない代替方法
   # （データ構造によっては困難）
   ```

**推奨:** Option A（許容する）- 主要な計算が正しければ実用上問題なし

---

### ❌ 問題: 型の不一致

**症状:**
```json
{
  "co2_amount": 6250,  // intではなくfloatが期待される
  "emission_factor": {  // 数値ではなくdictになっている
    "electricity": 0.5,
    "natural_gas": 2.03
  }
}
```

**原因1: JSON仕様による（問題なし）**

JSON仕様では `6250` と `6250.0` は同じ数値として扱われます。

**解決方法:** 問題なし、そのまま使用可能

**原因2: lookupが展開されていない**

emission_factorがlookupテーブル全体になっている場合：

**診断:**
```bash
# ルールを確認
grep -A 5 "emission_factor" output/ai_generated_rules.yaml
```

**解決方法:**

正しいlookup設定を使用：

```yaml
mapping:
  - target: emission_factor
    lookup:
      source: constants.emission_factors
      key_source: $.energy_type.name
      key_transform: lowercase_underscore
      default: 0.0
```

---

## ✅ Validator の問題

### ❌ 問題: 多数のエラーが報告される

**症状:**
```
Status: ❌ INVALID
Errors: 13
  - Type mismatches: 5
  - Null values: 4
  - Unknown properties: 4
```

**診断:**

詳細なレポートを確認：
```bash
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output.json \
    --report output/validation_report.txt

cat output/validation_report.txt
```

**一般的なエラーと解決方法:**

#### エラー1: 命名規則違反

```
❌ [ERROR] Field 'activityName' uses camelCase, should be 'activity_name'
```

**原因:** camelCaseがJSONデータに含まれている

**解決方法:**
1. ルールファイルでsnake_caseを使用
2. AIプロンプトが正しいことを確認（最新版は自動的に対応）

#### エラー2: 型の不一致

```
⚠️ [WARNING] Field 'co2_amount' is int, expected float
```

**原因:** JSON仕様の制限（intとfloatは区別されない）

**解決方法:** 問題なし、警告として扱う

#### エラー3: null値

```
⚠️ [WARNING] Field 'emission_source' is null
```

**原因:** rule_engineのparent context未サポート

**解決方法:** [null値が含まれる](#問題-null値が含まれる) を参照

---

### ❌ 問題: Strictモードで失敗

**症状:**
```bash
python jsonld_validator.py --strict [options]
# Status: ❌ INVALID (warnings are treated as errors)
```

**原因:** Strictモードでは警告もエラーとして扱われる

**解決方法:**

通常モードを使用：
```bash
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output.json
# Strictフラグなし
```

または、警告を修正：
1. null値を埋める（可能であれば）
2. 型を統一する
3. 未定義プロパティを削除

---

## 🌐 ネットワークとAPI の問題

### ❌ 問題: SSL証明書エラー

<a name="ssl-issues"></a>

**症状:**
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

**原因:** 企業プロキシやSSL検査が原因

**解決方法1: SSL検証を無効化（推奨）**

```bash
python ai_rule_generator.py --no-verify-ssl \
    model/source/manufacturing-ontology.ttl \
    model/target/ghg-report-ontology.ttl \
    output/ai_rules.yaml
```

**解決方法2: Pythonコードで**

```python
from ai_rule_generator import AIRuleGenerator

generator = AIRuleGenerator(
    source_ontology="source.ttl",
    target_ontology="target.ttl",
    verify_ssl=False  # SSL検証を無効化
)
```

**解決方法3: システムの証明書を更新**

```bash
# Ubuntu/Debian
sudo apt-get install ca-certificates
sudo update-ca-certificates

# macOS
# Keychain Access で証明書をインポート
```

---

### ❌ 問題: APIキーエラー

**症状:**
```
ValueError: ANTHROPIC_API_KEY environment variable or api_key parameter required
```

**原因:** APIキーが設定されていない

**解決方法1: 環境変数を設定**

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**解決方法2: コマンドライン引数**

```bash
python ai_rule_generator.py \
    source.ttl target.ttl output.yaml \
    your-api-key-here
```

**解決方法3: Pythonコード**

```python
generator = AIRuleGenerator(
    source_ontology="source.ttl",
    target_ontology="target.ttl",
    api_key="your-api-key-here"
)
```

**セキュリティ注意:**
- ✅ 環境変数を使用（推奨）
- ❌ コードに直接記述しない
- ❌ コマンドラインに直接記述しない（履歴に残る）

---

### ❌ 問題: API呼び出しエラー

**症状:**
```
Error: API call failed with status 429
```

**原因:** レート制限に達した

**解決方法:**
1. 数分待ってから再試行
2. APIキーのプランを確認
3. より低頻度でAPIを呼び出す

---

## 📊 データ構造の問題

### ❌ 問題: オントロジーとデータの命名規則が異なる

**問題:**

| オントロジー（RDF/Turtle） | 実際のJSON-LDデータ |
|--------------------------|-------------------|
| `mfg:hasEnergyConsumption` | `"energy_consumptions"` |
| `mfg:activityName` | `"activity_name"` |

**原因:** オントロジーはcamelCase、JSON-LDはsnake_case

**解決方法:**

完全な対応表は [RDF_JSON_LD_MAPPING.md](RDF_JSON_LD_MAPPING.md) を参照

**変換ルール:**
1. camelCase → snake_case
2. has + Name → 複数形配列
3. ネストされたオブジェクト内で簡略化

**例:**
```
hasEnergyConsumption → energy_consumptions (array)
activityName → activity_name
energyTypeName → name (inside energy_type object)
```

---

### ❌ 問題: 配列とオブジェクトの混在

**症状:**
```json
{
  "manufacturing_activities": [...]  // 配列
}
```

vs

```json
{
  "reporting_organization": {...}  // 単一オブジェクト
}
```

**原因:** データ構造の設計

**解決方法:**

ルールファイルで `iteration: true/false` を適切に設定：

```yaml
transformation_steps:
  - name: transform_activities
    source: manufacturing_activities
    iteration: true  # ✅ 配列を反復処理

  - name: map_organization
    source: organization
    iteration: false  # ✅ 単一オブジェクト
```

---

## 🔍 デバッグ手順

### 一般的なデバッグプロセス

1. **問題を特定**
   ```bash
   # 出力を確認
   cat output/ai_output.json | jq '.'

   # 期待値と比較
   cat output/correct_output.json | jq '.'
   ```

2. **ルールファイルを確認**
   ```bash
   # substeps
   grep -A 10 "substeps:" output/ai_generated_rules.yaml

   # calculation_rules
   grep -A 10 "calculation_rules:" output/ai_generated_rules.yaml

   # constants
   grep -A 10 "constants:" output/ai_generated_rules.yaml
   ```

3. **テストを実行**
   ```bash
   # 自動生成ロジックのテスト
   python test_improved_rule_generation.py

   # 完全テスト
   ./test_ai_generator.sh
   ```

4. **Validatorで検証**
   ```bash
   python jsonld_validator.py \
       model/target/ghg-report-ontology.ttl \
       output/ai_output.json \
       --report output/debug_report.txt

   cat output/debug_report.txt
   ```

5. **正解データと比較**
   ```bash
   diff <(jq -S . output/ai_output.json) <(jq -S . output/correct_output.json)
   ```

---

## 📚 関連ドキュメント

問題が解決しない場合は、以下のドキュメントも参照してください：

- [AI_RULE_GENERATOR.md](AI_RULE_GENERATOR.md) - AI生成の詳細
- [TESTING.md](TESTING.md) - テスト手順
- [TEST_RESULTS.md](TEST_RESULTS.md) - テスト結果の詳細
- [RDF_JSON_LD_MAPPING.md](RDF_JSON_LD_MAPPING.md) - 命名規則の詳細
- [VALIDATOR_README.md](VALIDATOR_README.md) - Validatorの詳細

---

## 💬 サポート

問題が解決しない場合：

1. GitHubでissueを作成
2. 以下の情報を含める：
   - エラーメッセージ
   - 使用したコマンド
   - 入力ファイル（可能であれば）
   - 期待される出力
   - 実際の出力

---

**作成日:** 2025-11-13
**最終更新:** 2025-11-13
**ステータス:** ✅ 完全
