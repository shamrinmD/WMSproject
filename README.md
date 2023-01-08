# WMSproject
Оптовая компания работает на рынке бытовой техники и электроники. Компания 
успешно развивает такие сегменты дистрибуции, как аудио/видео техника, крупная и 
малая бытовая техника. Компания работает как с мелкооптовыми, так и с 
крупнооптовыми покупателями. Информационные потребности определяют 
обширную информацию, определяющую реализацию процессов эффективной
обработки трех видов материальных потоков: входного (приемка товара), выходного 
(отгрузка товара) и внутреннего (размещение товара).
Целью является создание интерфейса для взаимодействия с базой данных складского учета. 
На складе организовано адресное хранение товаров для минимизации 
занимаемого свободного пространства и сокращения времени поиска товара. Вся 
работа с бумагами будет проводиться с использованием базы данных. При помощи 
базы данных на складе автоматизирован учет поступления и отгрузки товаров, учет 
входящих и исходящих документов, количественный учет. 

![Image alt](https://github.com/shamrinmD/WMSproject/blob/main/ERdiagram.PNG)

В системе существуют 4 типа ролей пользователей:

• Администратор БД

• Менеджер по закупкам

• Менеджер по продажам

• Старший кладовщик

Пользователи, которые появляются в системе, являются участниками 
определенных ролей. Каждая роль имеет свои привилегии. Администратор может 
регистрировать новых пользователей и выдавать им логин и пароль. Менеджер по 
закупкам может просмотреть накладные прихода и их детализацию. Он имеет доступ 
к информации о контрагентах, а также может корректировать справочник товаров. 
Менеджер по продажам имеет похожие привилегии, но работает он с накладными 
расхода и партиями отгрузки. Старший кладовщик заносит информацию в 
номенклатуру, обозначая приход и уход товара. Также кладовщик имеет доступ к 
таблице места хранения и может размещать товар на складе.
Кроме разграничения прав доступа и шифрования паролей, в системе 
присутствуют функции автоматического подсчета количества товара в базе данных и 
обновление данных о проведении накладных прихода и расхода.

Для создания графического интерфейса БД используется Flask — фреймворк для 
создания веб-приложений на языке программирования Python. Для подключения к 
PostgreSQL используется библиотека Psycopg. Менеджеры по продажам и закупкам 
имеют схожий интерфейс, который отличается только тем, что один пользователь 
занимается приходом товара на склад, а другой его выгрузкой.
