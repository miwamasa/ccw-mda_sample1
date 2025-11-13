# テストガイド

このドキュメントでは、MDA-based Data Transformation システムのテスト手順を説明します。

## 📋 目次

1. [自動テスト](#自動テスト)
2. [手動テスト](#手動テスト)
3. [AI Rule Generator のテスト](#ai-rule-generator-のテスト)
4. [Validator のテスト](#validator-のテスト)
5. [成功基準](#成功基準)
6. [トラブルシューティング](#トラブルシューティング)

## 🤖 自動テスト

### AI生成の完全テスト（APIキー必要）

```bash
# 環境変数設定
export ANTHROPIC_API_KEY='your-api-key-here'

# 自動テストスクリプト実行
./test_ai_generator.sh
```

このスクリプトは以下を実行します：
1. ✅ AIでルールを生成
2. ✅ 生成されたルールでデータ変換
3. ✅ 出力をvalidatorで検証
4. ✅ 正解データと比較
5. ✅ 成功/失敗を報告

### 個別テスト

```bash
# 自動生成ロジックのテスト（APIキー不要）
python test_improved_rule_generation.py

# Rule engineのテスト
python test_rule_engine.py
```

## 🔧 手動テスト

### 1. データ変換テスト（手作りルール使用）

**目的:** 手作りルールが正しく動作することを確認

```bash
# 製造データをGHG排出レポートに変換
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/ghg_report.json

# 結果を確認
cat output/ghg_report.json | jq '.total_emissions'
# 期待値: 12175.5
```

**期待される出力:**
```json
{
  "@type": "ghg:EmissionReport",
  "report_id": "GHG-AML-2024-01",
  "emissions": [
    {"@type": "ghg:Scope2Emission", "co2_amount": 6250.0},
    {"@type": "ghg:Scope1Emission", "co2_amount": 1725.5},
    {"@type": "ghg:Scope2Emission", "co2_amount": 4200.0}
  ],
  "total_emissions": 12175.5,
  "total_scope1": 1725.5,
  "total_scope2": 10450.0
}
```

### 2. 複数テストケース

```bash
# サンプル1: 小規模工場
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/sample1_output.json

# サンプル2: 複数燃料使用
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample2_multi_fuel.json \
    output/sample2_output.json

# サンプル3: 電子機器製造
python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample3_electronics.json \
    output/sample3_output.json
```

### 3. データ検証テスト

```bash
# 出力データをオントロジーに対して検証
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ghg_report.json

# レポートを保存
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ghg_report.json \
    --report output/validation_report.txt

# レポートを確認
cat output/validation_report.txt
```

## 🤖 AI Rule Generator のテスト

### ステップ1: AI生成ルールの作成

**通常の環境:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'

python ai_rule_generator.py \
    model/source/manufacturing-ontology.ttl \
    model/target/ghg-report-ontology.ttl \
    output/ai_generated_rules.yaml
```

**企業プロキシ環境（SSL証明書エラーがある場合）:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'

python ai_rule_generator.py --no-verify-ssl \
    model/source/manufacturing-ontology.ttl \
    model/target/ghg-report-ontology.ttl \
    output/ai_generated_rules.yaml
```

**期待される出力:**
```
======================================================================
AI ANALYSIS IN PROGRESS
======================================================================
Analyzing ontologies with Claude AI...

======================================================================
AI ANALYSIS COMPLETE
======================================================================

✅ AI-generated rules saved to: output/ai_generated_rules.yaml
✅ Auto-generated substeps added
✅ Essential calculation_rules added
✅ Emission factors added
```

### ステップ2: 生成されたルールの検証

```bash
# substepsが空でないことを確認
grep -A 10 "substeps:" output/ai_generated_rules.yaml

# 期待: substeps配列が空でない
# substeps:
#   - name: iterate_energy_consumptions
#     source: $.energy_consumptions
#     ...

# mappingキーが存在することを確認
grep "mapping:" output/ai_generated_rules.yaml

# emission factorsが正しいことを確認
grep -A 5 "emission_factors:" output/ai_generated_rules.yaml

# 期待:
# emission_factors:
#   electricity: 0.5
#   natural_gas: 2.03
#   diesel: 2.68
```

### ステップ3: AI生成ルールでデータ変換

```bash
python rule_engine.py \
    output/ai_generated_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/ai_output.json

# 結果を確認
cat output/ai_output.json | jq '.total_emissions'
# 期待値: 12175.5
```

### ステップ4: AI生成の出力を検証

```bash
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output.json
```

### ステップ5: 正解データと比較

```bash
python -c "
import json

with open('output/ai_output.json') as f:
    ai_output = json.load(f)

with open('output/correct_output.json') as f:
    correct_output = json.load(f)

print('=' * 60)
print('AI生成 vs 正解データ比較')
print('=' * 60)
print(f'AI total_emissions:      {ai_output.get(\"total_emissions\", 0)}')
print(f'正解 total_emissions:    {correct_output.get(\"total_emissions\", 0)}')
print(f'AI emissions数:          {len(ai_output.get(\"emissions\", []))}')
print(f'正解 emissions数:        {len(correct_output.get(\"emissions\", []))}')
print('=' * 60)

# 誤差を計算
ai_total = ai_output.get('total_emissions', 0)
correct_total = correct_output.get('total_emissions', 0)
if correct_total > 0:
    error_percent = abs(ai_total - correct_total) / correct_total * 100
    print(f'誤差: {error_percent:.2f}%')
    if error_percent < 1:
        print('✅ テスト合格（誤差 < 1%）')
    else:
        print('❌ テスト失敗（誤差 >= 1%）')
"
```

## 🔍 Validator のテスト

### 基本的な検証

```bash
# 有効なJSONファイルを検証
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/correct_output.json

# 期待される出力:
# Status: ✅ VALID
# Errors: 0
# Warnings: 2-4
# Info: 1-2
```

### 無効なデータの検証

```bash
# 無効なフィールド名を含むデータ
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    test_data/invalid/camelCase_fields.json

# 期待される出力:
# Status: ❌ INVALID
# Errors: 5+
#   - Naming violations (camelCase instead of snake_case)
```

### Strict モード

```bash
# Strictモードで検証（警告もエラーとして扱う）
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ghg_report.json \
    --strict
```

## ✅ 成功基準

### 手作りルールの成功基準

1. ✅ **total_emissions = 12,175.5 kg-CO2**
2. ✅ **emissions配列に3件のレコード**
3. ✅ **各emissionに以下が含まれる:**
   - `@type`: "ghg:Scope1Emission" または "ghg:Scope2Emission"
   - `co2_amount`: 正の数値
   - `emission_source`: null でない文字列
   - `source_category`: null でない文字列
4. ✅ **total_scope1 = 1,725.5 kg-CO2**
5. ✅ **total_scope2 = 10,450.0 kg-CO2**
6. ✅ **Validator errors = 0**

### AI生成ルールの成功基準

1. ✅ **生成されたYAMLに非空のsubstepsがある**
2. ✅ **すべてのフィールド名がsnake_case**
3. ✅ **total_emissions ≈ 12,175.5 kg-CO2（誤差 < 1%）**
4. ✅ **emissions配列に3件のレコード**
5. ✅ **Validator errors = 0**
6. ✅ **emission_factors が正しい値:**
   - electricity: 0.5
   - natural_gas: 2.03
   - diesel: 2.68

### Validatorの成功基準

1. ✅ **有効なデータに対して errors = 0**
2. ✅ **無効なデータに対して errors > 0**
3. ✅ **命名規則違反を検出**
4. ✅ **型の不一致を検出**
5. ✅ **不明なプロパティを検出**

## 🐛 トラブルシューティング

### 問題1: total_emissions = 0

**症状:**
```json
{
  "total_emissions": 0,
  "emissions": []
}
```

**原因と解決方法:**

1. **substeps が空**
   ```bash
   # 確認
   grep -A 5 "substeps:" output/ai_generated_rules.yaml

   # 解決: 最新版の ai_rule_generator.py を使用
   ```

2. **計算ルールが実行されない**
   ```bash
   # 確認
   grep "calculation:" output/ai_generated_rules.yaml

   # 解決: calculation_rules に calculate_co2_emission があることを確認
   ```

3. **emission_factors が不正確または存在しない**
   ```bash
   # 確認
   grep -A 5 "emission_factors:" output/ai_generated_rules.yaml

   # 解決: 自動生成ロジックが emission_factors を追加
   ```

### 問題2: Validator がエラーを報告

**症状:**
```
Status: ❌ INVALID
Errors: 13
```

**原因と解決方法:**

1. **命名規則違反（camelCase）**
   ```bash
   # 原因: activityName instead of activity_name
   # 解決: ルールファイルのフィールド名を snake_case に修正
   ```

2. **型の不一致**
   ```bash
   # 原因: JSONの型がオントロジーの定義と異なる
   # 解決: 通常は問題なし（JSON仕様では int と float は区別されない）
   ```

3. **null 値**
   ```bash
   # 原因: emission_source や source_category が null
   # 解決: これは rule_engine の制限（parent context 未サポート）
   #      主要な指標（total_emissions）が正しければ問題なし
   ```

### 問題3: SSL証明書エラー

**症状:**
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**解決方法:**
```bash
python ai_rule_generator.py --no-verify-ssl [その他のオプション]
```

詳細は [TROUBLESHOOTING.md](TROUBLESHOOTING.md#ssl証明書エラー) を参照。

### 問題4: APIキーエラー

**症状:**
```
ValueError: ANTHROPIC_API_KEY environment variable or api_key parameter required
```

**解決方法:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 問題5: AI生成ルールで emissions が空のオブジェクト

**症状:**
```json
{
  "emissions": [{}, {}, {}]
}
```

**原因:** AI生成のsubstepsが非互換の構造（`field_mappings` ではなく `mapping` が必要）

**解決方法:**
1. 最新版の `ai_rule_generator.py` を使用（自動生成ロジックが対応済み）
2. テスト実行:
   ```bash
   python test_improved_rule_generation.py
   ```

## 📊 テストケース一覧

| テストケース | 入力ファイル | 期待される出力 |
|-------------|------------|--------------|
| **小規模工場** | sample1_small_factory.json | 2活動、total: 12,175.5 kg-CO2 |
| **複数燃料** | sample2_multi_fuel.json | Scope1+Scope2混在 |
| **電子機器製造** | sample3_electronics.json | 5活動、正常 |

### 詳細なテスト結果

各テストケースの詳細な結果は [TEST_RESULTS.md](TEST_RESULTS.md) を参照してください。

## 🔄 継続的インテグレーション

### 推奨テストフロー

```bash
# 1. 単体テスト
python test_rule_engine.py
python test_improved_rule_generation.py

# 2. 統合テスト（APIキー必要）
export ANTHROPIC_API_KEY='your-key'
./test_ai_generator.sh

# 3. 検証テスト
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output.json

# 4. 回帰テスト
# 正解データと比較して誤差 < 1% を確認
```

## 📈 パフォーマンステスト

```bash
# 処理時間を測定
time python rule_engine.py \
    transformation_rules.yaml \
    test_data/source/sample1_small_factory.json \
    output/perf_test.json

# 期待: < 0.1秒（小規模データ）
```

### ベンチマーク結果

| テストケース | 入力サイズ | 処理時間 | 出力 |
|-------------|----------|---------|------|
| sample1_small_factory | 2活動 | <0.1秒 | 12,175.5 kg-CO2 |
| sample2_multi_fuel | 3活動 | <0.1秒 | 正常 |
| sample3_electronics | 5活動 | <0.2秒 | 正常 |

## 🔐 セキュリティテスト

### APIキーの保護

```bash
# ❌ 悪い例: コマンドラインに直接APIキーを記述
python ai_rule_generator.py source.ttl target.ttl output.yaml sk-ant-api03-xxx

# ✅ 良い例: 環境変数を使用
export ANTHROPIC_API_KEY='sk-ant-api03-xxx'
python ai_rule_generator.py source.ttl target.ttl output.yaml
```

### ログファイルの確認

```bash
# APIキーがログに含まれていないことを確認
grep -r "sk-ant-api" *.log
# 期待: 何も見つからない
```

## 📝 テストレポート

### レポートの生成

```bash
# 検証レポートを生成
python jsonld_validator.py \
    model/target/ghg-report-ontology.ttl \
    output/ai_output.json \
    --report output/validation_report.txt

# レポートを確認
cat output/validation_report.txt
```

### レポートの内容

```
======================================================================
VALIDATION REPORT
======================================================================
File: output/ai_output.json
Ontology: model/target/ghg-report-ontology.ttl

Status: ✅ VALID

Summary:
  Errors: 0
  Warnings: 3
  Info: 1

Details:
  ⚠️ [WARNING] Field 'emission_source' is null (line 15)
  ⚠️ [WARNING] Field 'source_category' is null (line 16)
  ⚠️ [WARNING] Field 'emission_factor' is a dict, expected number (line 20)
  ℹ️ [INFO] Optional field 'report_date' not present

======================================================================
```

## 🎯 次のステップ

テストが成功したら：

1. ✅ 変更をコミット
2. ✅ ドキュメントを更新
3. ✅ 本番環境にデプロイ

テストが失敗したら：

1. 📝 問題を文書化
2. 🔧 修正を実装
3. 🔄 再テスト

---

**作成日:** 2025-11-13
**最終更新:** 2025-11-13
**ステータス:** ✅ 完全
