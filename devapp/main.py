from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2

app = Flask(__name__)
app.secret_key = 'misya'

db_host = 'localhost'
db_name = 'wms'
db_user = 'postgres'
db_pass = '180714qw'
db_port = 5432


@app.route('/')
def home():
    """Главная страница"""
    # Проверяем авторизацию пользователя
    if 'loggedin' in session:
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        purchasing_manager = False
        sales_manager = False
        storekeeper = False
        table = None
        nomenclature = None
        # Проверка прав доступа пользователя
        if session['role'] == 'Менеджер по продажам':
            sales_manager = True
            # Вывод ухода
            cursor.execute('SELECT * FROM leaving_view ORDER BY reg_date DESC')
            table = cursor.fetchall()
        elif session['role'] == 'Менеджер по закупкам':
            purchasing_manager = True
            # Вывод прихода
            cursor.execute('SELECT * FROM supply_view ORDER BY reg_date DESC')
            table = cursor.fetchall()
        else:
            storekeeper = True
            # Вывод всей номенклатуры
            cursor.execute('SELECT * FROM nomenclature_view')
            nomenclature = cursor.fetchall()
        return render_template('home.html', loggedin=session['loggedin'],
                               purchasing_manager=purchasing_manager,
                               sales_manager=sales_manager,
                               storekeeper=storekeeper,
                               username=session['role'], table=table, nomenclature=nomenclature)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Авторизация"""
    if request.method == 'POST':
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        login = request.form['auth_login']
        password = request.form['auth_password']
        user = None
        hash_pwd = None
        # Ищем пользователя в БД
        cursor.execute('SELECT * FROM users_info WHERE login = %s', (login,))
        user = cursor.fetchone()
        # Поиск хэшированного пароля
        cursor.execute('SELECT (hash_pass = crypt(%s, hash_pass)) AS pass FROM users_info WHERE login = %s',
                       (password, login,))
        hash_pwd = cursor.fetchone()
        # Поиск должности работника
        cursor.execute('SELECT post FROM users_info WHERE login = %s', (login,))
        role = cursor.fetchone()[0]
        # Проверяем существование пользователя в БД
        if user:
            if hash_pwd:
                session['loggedin'] = True
                session['username'] = login
                session['pass'] = password
                session['role'] = role
                return redirect(url_for('home'))
            else:
                flash('Неверный логин или пароль')
                return redirect(url_for('login'))
        else:
            flash('Такого пользователя не существует')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/show_arrival_waybill/<string:waybill_id>')
def show_arrival_waybill(waybill_id):
    """Страница с информацией о накладной прихода"""
    if ('loggedin' in session) and (session['role'] == 'Менеджер по закупкам'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Вывод основной информации о накладной прихода по ее номеру
        cursor.execute('SELECT * FROM arrival_waybills_view WHERE waybill_id = %s', (waybill_id,))
        waybill = cursor.fetchone()
        # Вывод содержимого накладной прихода (партии товара)
        cursor.execute('SELECT product_name, measure_unit, quantity, weight, volume FROM supply_view \
                       WHERE waybill_id = %s', (waybill_id,))
        supply = cursor.fetchall()
        # Вывод номенклатуры прихода по данной накладной
        cursor.execute('SELECT serial_№, category, product_name, volume, date_supply FROM nomenclature_view \
                        WHERE arrival_waybill = %s', (waybill_id,))
        nomenclature = cursor.fetchall()
        return render_template('show_arrival_waybill.html', waybill=waybill, supply=supply, nomenclature=nomenclature,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/show_sale_waybill/<string:waybill_id>')
def show_sale_waybill(waybill_id):
    """Страница с информацией о расходной накладной"""
    if ('loggedin' in session) and (session['role'] == 'Менеджер по продажам'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Вывод основной информации о накладной расхода по ее номеру
        cursor.execute('SELECT * FROM sale_waybills_view WHERE waybill_id = %s', (waybill_id,))
        waybill = cursor.fetchone()
        # Вывод содержимого расходной накладной (партии товара)
        cursor.execute('SELECT product_name, measure_unit, quantity, weight, volume FROM leaving_view \
                       WHERE waybill_id = %s', (waybill_id,))
        leave = cursor.fetchall()
        # Вывод номенклатуры ухода по накладной расхода
        cursor.execute('SELECT serial_№, category, product_name, volume, date_leave FROM nomenclature_view \
                        WHERE sale_waybill = %s', (waybill_id,))
        nomenclature = cursor.fetchall()
        return render_template('show_sale_waybill.html', waybill=waybill, leave=leave, nomenclature=nomenclature,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/arrival_waybills', methods=['GET', 'POST'])
def arrival_waybills():
    """Страница накладных прихода"""
    if ('loggedin' in session) and (session['role'] == 'Менеджер по закупкам'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Поиск всех накладных прихода
        cursor.execute('SELECT * FROM arrival_waybills_view')
        waybill = cursor.fetchall()
        # Вывод информации о поставщиках
        cursor.execute('SELECT org_id, org_name FROM contractors')
        org = cursor.fetchall()
        if request.method == 'POST':
            waybill_id = request.form.get('waybill_id')
            reg_date = request.form.get('reg_date')
            description = request.form.get('description')
            contractor = request.form.get('contractor')
            if waybill_id and reg_date and description and contractor:
                # Вызов процедуры добавления накладной прихода
                cursor.execute('CALL add_arrival_waybill(%s,%s,%s,%s)',
                               (waybill_id, reg_date, description, contractor,))
                conn.commit()
                flash('Накладная создана!')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('arrival_waybills.html', waybill=waybill, contractors=org,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/sale_waybills', methods=['GET', 'POST'])
def sale_waybills():
    """Страница расходных накладных"""
    if ('loggedin' in session) and (session['role'] == 'Менеджер по продажам'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Поиск всех расходных накладных
        cursor.execute('SELECT * FROM sale_waybills_view')
        waybill = cursor.fetchall()
        # Вывод информации о получателях
        cursor.execute('SELECT org_id, org_name FROM contractors')
        org = cursor.fetchall()
        if request.method == 'POST':
            waybill_id = request.form.get('waybill_id')
            reg_date = request.form.get('reg_date')
            description = request.form.get('description')
            contractor = request.form.get('contractor')
            if waybill_id and reg_date and description and contractor:
                # Вызов процедуры добавления расходной накладной
                cursor.execute('CALL add_sale_waybill(%s,%s,%s,%s)',
                               (waybill_id, reg_date, description, contractor,))
                conn.commit()
                flash('Накладная создана!')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('sale_waybills.html', waybill=waybill, contractors=org,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/remnants', methods=['GET', 'POST'])
def remnants():
    """Остатки товаров"""
    if ('loggedin' in session) and ((session['role'] == 'Менеджер по закупкам') or
                                    (session['role'] == 'Менеджер по продажам')):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        cursor.execute('SELECT product_code, product_name FROM product_view')
        products = cursor.fetchall()
        # Получение информации о текущих остатках товара на складе
        cursor.execute('SELECT * FROM get_current_remnants()')
        remnant = cursor.fetchall()
        if request.method == 'POST':
            date_remnant = request.form.get('date_remnant')
            product_code = request.form.get('product_code')
            directory = request.form.get('directory')
            if date_remnant and product_code and directory:
                # Вызов процедуры выгрузки отчета об остатках конкретного товара
                cursor.execute('CALL report_product_remnants(%s,%s,%s)',
                               (product_code, date_remnant, directory,))
                conn.commit()
            elif date_remnant and directory and (product_code == ''):
                # Вызов процедуры выгрузки отчета об остатках товаров по конкретной дате
                cursor.execute('CALL report_date_remnants(%s,%s)',
                               (date_remnant, directory,))
                conn.commit()
            elif product_code and directory and (date_remnant == ''):
                flash('Пожалуйста, заполните дату!')
            elif (product_code == '') and directory and (date_remnant == ''):
                # Вызов процедуры выгрузки отчета о текущих остатках товаров на складе
                cursor.execute('CALL report_current_remnants(%s)', (directory,))
                conn.commit()
            else:
                flash('Пожалуйста, заполните данные!')
        return render_template('remnants.html', products=products, remnant=remnant,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/accept_product')
def accept_product():
    """Приемка товара на склад"""
    if ('loggedin' in session) and (session['role'] == 'Старший кладовщик'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Вывод всех партий прихода на склад
        cursor.execute('SELECT * FROM supply_view WHERE completed = false ORDER BY reg_date DESC')
        supply = cursor.fetchall()
        return render_template('accept_product.html', supply=supply,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/send_product')
def send_product():
    """Отгрузка товара со склада"""
    if ('loggedin' in session) and (session['role'] == 'Старший кладовщик'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Вывод всех партий отгрузки со склада
        cursor.execute('SELECT * FROM leaving_view WHERE completed = false ORDER BY reg_date DESC')
        leave = cursor.fetchall()
        return render_template('send_product.html', leave=leave,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/find_product/<string:waybill_id>, <string:product_name>', methods=['GET', 'POST'])
def find_product(waybill_id, product_name):
    """Поиск товара"""
    if ('loggedin' in session) and (session['role'] == 'Старший кладовщик'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Поиск товара по его названию
        cursor.execute('SELECT product_code, product_name FROM product_view WHERE (product_name = %s)', (product_name,))
        product = cursor.fetchone()
        # Вывод товара для отгрузки
        cursor.execute('SELECT * FROM send_product(%s,%s)', (waybill_id, product[0],))
        nomenclature = cursor.fetchall()
        if request.method == 'POST':
            for n in nomenclature:
                # Вызов процедуры освобождения ячейки хранения товара на складе
                cursor.execute('CALL release_place_one(%s)', (n[0],))
            conn.commit()
            flash('Ячейки освобождены!')
        return render_template('find_product.html', nomenclature=nomenclature, waybill_id=waybill_id,
                               product_name=product[1], loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/add_nomenclature/<string:waybill_id>, <string:product_name>', methods=['GET', 'POST'])
def add_nomenclature(waybill_id, product_name):
    """Добавить единицу товара прихода"""
    if ('loggedin' in session) and (session['role'] == 'Старший кладовщик'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Вывод всей номенклатуры по накладной прихода
        cursor.execute('SELECT * FROM nomenclature_view WHERE (arrival_waybill = %s) AND (product_name = %s)',
                       (waybill_id, product_name,))
        nomenclature = cursor.fetchall()
        cursor.execute('SELECT product_code, product_name FROM product_view WHERE (product_name = %s)', (product_name,))
        product = cursor.fetchone()
        # Вывод информации о поставке товара на склад
        cursor.execute('SELECT supply_id, quantity FROM supply WHERE (waybill_id = %s) AND (product_id = %s)',
                       (waybill_id, product[0],))
        supply = cursor.fetchone()
        # Счетчик товара прихода в номенклатуре
        cursor.execute('SELECT COUNT(*) FROM nomenclature_unit WHERE supply = %s', (supply[0],))
        count = cursor.fetchone()[0]
        if request.method == 'POST':
            serial = request.form.get('serial')
            if serial:
                # Проверка кол-ва товара прихода на склад
                if supply[1] > count:
                    # Вызов процедуры добавления товарной единицы
                    cursor.execute('CALL add_nomenclature_unit(%s,%s,%s)', (serial, product[0], supply[0],))
                    conn.commit()
                    flash('Товарная единица добавлена')
                else:
                    flash('Вы не можете больше добавить товара')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('add_nomenclature.html', nomenclature=nomenclature, waybill_id=waybill_id,
                               product_name=product[1], quantity=supply[1], loggedin=session['loggedin'],
                               username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/place_product/<string:waybill_id>, <string:product_name>', methods=['GET', 'POST'])
def place_product(waybill_id, product_name):
    """Размещение товара на складе"""
    if ('loggedin' in session) and (session['role'] == 'Старший кладовщик'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о товаре прихода
        cursor.execute('SELECT * FROM nomenclature_view WHERE (arrival_waybill = %s) AND (product_name = %s)',
                       (waybill_id, product_name,))
        nomenclature = cursor.fetchall()
        # Информация о объеме товара прихода
        cursor.execute('SELECT volume FROM product_info WHERE product_name = %s', (product_name,))
        product_volume = cursor.fetchone()[0]
        # Информация о свободных ячейках на складе
        cursor.execute('SELECT * FROM get_free_cells() ORDER BY shelf_id, cell_id ASC')
        storage = cursor.fetchall()
        # Номер ячейки
        cursor.execute('SELECT DISTINCT cell_id  FROM get_free_cells() ORDER BY cell_id ASC')
        cell_select = cursor.fetchall()
        # Номер стеллажа
        cursor.execute('SELECT DISTINCT shelf_id  FROM get_free_cells() ORDER BY shelf_id ASC')
        shelf_select = cursor.fetchall()
        if request.method == 'POST':
            serial = request.form.get('serial')
            cell = request.form.get('cell')
            shelf = request.form.get('shelf')
            # Текущий объем ячейки
            cursor.execute('SELECT current_volume FROM storage_address WHERE (cell_id = %s) \
                           AND (shelf_id = %s)', (cell, shelf,))
            volume = cursor.fetchone()[0]
            # Сравнение объема товара и ячейки склада
            if volume >= product_volume:
                # Вызов процедуры размещения товара на складе
                cursor.execute('CALL place_product(%s,%s,%s)', (serial, cell, shelf,))
                conn.commit()
                flash('Товар размещен!')
            else:
                flash('Вы не можете разместить товар в этой ячейке!')
        return render_template('place_product.html', nomenclature=nomenclature, waybill_id=waybill_id,
                               cell_select=cell_select, shelf_select=shelf_select, storage=storage,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/auto_place/<string:waybill_id>, <string:product_name>', methods=['GET', 'POST'])
def auto_place(waybill_id, product_name):
    """Автоматическое размещение товара на складе"""
    if ('loggedin' in session) and (session['role'] == 'Старший кладовщик'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о товаре прихода
        cursor.execute('SELECT * FROM nomenclature_view WHERE (arrival_waybill = %s) AND (product_name = %s)',
                       (waybill_id, product_name,))
        nomenclature = cursor.fetchall()
        for n in nomenclature:
            # Вызов процедуры авторазмещения товара на складе
            cursor.execute('CALL auto_place_one(%s)', (n[0],))
        conn.commit()
        flash('Товар размещен!')
        cursor.execute('SELECT * FROM nomenclature_view WHERE (arrival_waybill = %s) AND (product_name = %s)',
                       (waybill_id, product_name,))
        nomenclature = cursor.fetchall()
        return render_template('auto_place.html', nomenclature=nomenclature, waybill_id=waybill_id,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/add_leave', methods=['GET', 'POST'])
def add_leave():
    """Создание партии товара ухода со склада"""
    if ('loggedin' in session) and (session['role'] == 'Менеджер по продажам'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о расходной накладной
        cursor.execute('SELECT waybill_id, recipient FROM sale_waybills_view WHERE completed = false')
        waybill = cursor.fetchall()
        cursor.execute('SELECT product_code, product_name FROM product_view')
        products = cursor.fetchall()
        if request.method == 'POST':
            product_code = request.form.get('product_code')
            waybill_id = request.form.get('waybill_id')
            quantity = request.form.get('quantity')
            if product_code and waybill_id and quantity:
                # Счетчик товара отгрузки в номенклатуре
                cursor.execute('SELECT COUNT(*) FROM nomenclature_unit WHERE product_id = %s', (product_code,))
                count = cursor.fetchone()[0]
                # Проверка кол-ва товара отгрузки со склада
                if int(quantity) <= count:
                    # Вызов процедуры добавления партии отгрузки
                    cursor.execute('CALL add_leaving(%s,%s,%s)',
                                   (product_code, waybill_id, quantity,))
                    conn.commit()
                    flash('Партия отгрузки создана!')
                else:
                    flash('Вы не можете столько отгрузить товара')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('leave.html', waybill=waybill, product=products,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/add_supply', methods=['GET', 'POST'])
def add_supply():
    """Создание партии товара прихода на склад"""
    if ('loggedin' in session) and (session['role'] == 'Менеджер по закупкам'):
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о накладной прихода
        cursor.execute('SELECT waybill_id, provider FROM arrival_waybills_view WHERE completed = false')
        waybill = cursor.fetchall()
        cursor.execute('SELECT product_code, product_name FROM product_view')
        products = cursor.fetchall()
        if request.method == 'POST':
            product_code = request.form.get('product_code')
            waybill_id = request.form.get('waybill_id')
            quantity = request.form.get('quantity')
            if product_code and waybill_id and quantity:
                # Вызов процедуры добавления партии ожидаемого прихода на склад
                cursor.execute('CALL add_supply(%s,%s,%s)', (product_code, waybill_id, quantity,))
                conn.commit()
                flash('Партия прихода создана!')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('supply.html', waybill=waybill, product=products,
                               loggedin=session['loggedin'], username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/warehouse', methods=['GET', 'POST'])
def warehouse():
    """Страница с информацией о складе"""
    if 'loggedin' in session:
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о ячейках и стеллажах на складе
        cursor.execute('SELECT cell_id, shelf_id, current_volume FROM storage_address ORDER BY shelf_id ASC')
        table = cursor.fetchall()
        storekeeper = False
        if session['role'] == 'Старший кладовщик':
            storekeeper = True
        if request.method == 'POST':
            cell_id = int(request.form.get('cell_id'))
            shelf_id = int(request.form.get('shelf_id'))
            volume = float(request.form.get('volume'))
            if cell_id and shelf_id and volume:
                # Вызов процедуры создания новой ячейки на складе
                cursor.execute('CALL add_storage_address(%s,%s,%s)',
                               (cell_id, shelf_id, volume,))
                conn.commit()
                flash('Ячейка добавлена!')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('warehouse.html', table=table, loggedin=session['loggedin'],
                               storekeeper=storekeeper, username=session['role'])
    else:
        return redirect(url_for('logout'))


@app.route('/product', methods=['GET', 'POST'])
def product():
    """Страница справочника товара"""
    if session['loggedin']:
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о товаре (телевизоре)
        cursor.execute('SELECT * FROM product_view')
        table = cursor.fetchall()
        if request.method == 'POST':
            product_code = int(request.form.get('product_code'))
            category = int(request.form.get('category'))
            product_name = request.form.get('product_name')
            diagonal = int(request.form.get('diagonal'))
            weight = float(request.form.get('weight'))
            volume = float(request.form.get('volume'))
            if product_code and category and product_name and diagonal and weight \
                    and volume:
                # Вызов процедуры добавления нового товара в справочник
                cursor.execute('CALL add_product_info(%s,%s,%s,%s,%s,%s)',
                               (product_code, product_name, weight, volume, category, diagonal,))
                conn.commit()
                flash('Товар добавлен!')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('product.html', username=session['username'], loggedin=session['loggedin'], table=table)
    else:
        return redirect(url_for('logout'))


@app.route('/contractors', methods=['GET', 'POST'])
def contractors():
    """Страница с информацией о контрагентах"""
    if session['loggedin']:
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о контрагентах
        cursor.execute('SELECT * FROM contractors')
        table = cursor.fetchall()
        storekeeper = False
        if session['role'] == 'Старший кладовщик':
            storekeeper = True
        if request.method == 'POST':
            org_code = request.form.get('org_code')
            org_name = request.form.get('org_name')
            org_address = request.form.get('org_address')
            city = request.form.get('city')
            org_phone = request.form.get('org_phone')
            email = request.form.get('email')
            if org_code and org_name and org_address and city and org_phone \
                    and email:
                # Вызов процедуры добавления нового контрагента в БД
                cursor.execute('CALL add_contractor(%s,%s,%s,%s,%s,%s)',
                               (org_code, org_name, org_address, city, org_phone, email,))
                conn.commit()
                flash('Контрагент добавлен!')
            else:
                flash('Пожалуйста, заполните все данные!')
        return render_template('contractors.html', username=session['username'], loggedin=session['loggedin'],
                               storekeeper=storekeeper, table=table)
    else:
        return redirect(url_for('logout'))


@app.route('/about_me')
def about_me():
    """Страница с информацией о работнике"""
    if 'loggedin' in session:
        db_user = session['username']
        db_pass = session['pass']
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_pass, host=db_host)
        cursor = conn.cursor()
        # Информация о работнике
        cursor.execute('SELECT first_name, middle_name, last_name, post, phone, email FROM users_info WHERE login = %s',
                       (db_user,))
        user_info = cursor.fetchone()
        return render_template('about_me.html', user_info=user_info, loggedin=session['loggedin'],
                               username=session['role'])
    else:
        return redirect(url_for('logout'))


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
