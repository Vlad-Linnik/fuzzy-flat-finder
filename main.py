from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

importance_map = {
    'Неважливо': 0,
    'Середня важливість': 0.5,
    'Дуже важливо': 1
}

def convert(importance):
    return importance_map.get(importance, 0)

def fuzzy_score(user, df):
    df = df.rename(columns={
        'Ціна': 'Ціна',
        'Площа': 'Площа',
        'Кімнати': 'Кімнати',
        'Поверх': 'Поверх',
        'Поверховість': 'Поверховість',
        'район': 'Район',
        'тип': 'Тип',
        'Рік': 'Рік',
        'стан': 'Стан',
        'Відстань': 'Відстань'
    })

    scores = []
    norm = {
        'Ціна': (df['Ціна'].min(), df['Ціна'].max()),
        'Площа': (df['Площа'].min(), df['Площа'].max()),
        'Кімнати': (df['Кімнати'].min(), df['Кімнати'].max()),
        'Поверх': (df['Поверх'].min(), df['Поверх'].max()),
        'Поверховість': (df['Поверховість'].min(), df['Поверховість'].max()),
        'Рік': (df['Рік'].min(), df['Рік'].max()),
        'Відстань': (df['Відстань'].min(), df['Відстань'].max())
    }

    for _, row in df.iterrows():
        total_score = 0
        total_weight = 0

        # Кількісні параметри
        for key_csv, key_form, fuzzy_key in [
            ('Ціна', 'price', 'price_fuzzy'),
            ('Площа', 'area', 'area_fuzzy'),
            ('Кімнати', 'rooms', 'rooms_fuzzy'),
            ('Поверх', 'floor', 'floor_fuzzy'),
            ('Поверховість', 'floors_total', 'floors_total_fuzzy'),
            ('Рік', 'year', 'year_fuzzy'),
            ('Відстань', 'distance', 'distance_fuzzy')
        ]:
            weight = convert(user.get(fuzzy_key, 'Неважливо'))
            if weight == 0:
                continue
            u_val = float(user[key_form])
            r_val = row[key_csv]
            min_v, max_v = norm[key_csv]
            diff = abs(u_val - r_val) / (max_v - min_v + 1e-5)
            score = 1 - diff
            total_score += score * weight
            total_weight += weight

        # Категоріальні параметри з вагами
        for key_csv, key_form, fuzzy_key in [
            ('Район', 'district', 'district_fuzzy'),
            ('Тип', 'type', 'type_fuzzy'),
            ('Стан', 'condition', 'condition_fuzzy')
        ]:
            weight = convert(user.get(fuzzy_key, 'Неважливо'))
            if weight == 0:
                continue
            match = 1 if user[key_form].strip().lower() == str(row[key_csv]).strip().lower() else 0
            total_score += match * weight
            total_weight += weight

        scores.append(total_score / total_weight if total_weight > 0 else 0)

    df['Оцінка'] = scores
    return df.sort_values(by='Оцінка', ascending=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        preferences = {
            'price': request.form.get('price'),
            'price_fuzzy': request.form.get('price_fuzzy'),
            'area': request.form.get('area'),
            'area_fuzzy': request.form.get('area_fuzzy'),
            'rooms': request.form.get('rooms'),
            'rooms_fuzzy': request.form.get('rooms_fuzzy'),
            'floor': request.form.get('floor'),
            'floor_fuzzy': request.form.get('floor_fuzzy'),
            'floors_total': request.form.get('floors_total'),
            'floors_total_fuzzy': request.form.get('floors_total_fuzzy'),
            'district': request.form.get('district'),
            'district_fuzzy': request.form.get('district_fuzzy'),
            'type': request.form.get('type'),
            'type_fuzzy': request.form.get('type_fuzzy'),
            'year': request.form.get('year'),
            'year_fuzzy': request.form.get('year_fuzzy'),
            'condition': request.form.get('condition'),
            'condition_fuzzy': request.form.get('condition_fuzzy'),
            'distance': request.form.get('distance'),
            'distance_fuzzy': request.form.get('distance_fuzzy')
        }

        df = pd.read_csv('data/apartments.csv')
        result_df = fuzzy_score(preferences, df)

        # Словник візуальних назв
        display_names = {
            'Ціна': 'Ціна $',
            'Відстань': 'Відстань до центру (хв)',
            'Оцінка': 'Оцінка',
        }

        return render_template(
            'results.html',
            preferences=preferences,
            convert=convert,
            table=result_df.head(10).to_dict(orient='records'),
            columns=result_df.columns,
            display_names=display_names
        )

    return render_template('form.html')


if __name__ == '__main__':
    app.run(debug=True)
