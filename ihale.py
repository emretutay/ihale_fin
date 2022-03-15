


from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,DateTimeField,IntegerField,SelectField,BooleanField
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu işlemi yapmak için admin olmanız gerekmektedir.","danger")
            return redirect(url_for("login"))

    return decorated_function
def register_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("register"))

    return decorated_function

class IhaleFormu(Form):
    title = StringField("İhale Başlığı",validators=[validators.Length(min = 1,max = 100)]) 
    content = TextAreaField("İhale Açıklaması",validators=[validators.Length(min = 5,max = 300)]) 
    end_date = DateTimeField("Bitiş Tarihi",display_format = '%Y-%m-%d %H:%M') 
    category = SelectField(u'İhale Kategorisi',choices = [("ev","ev"),("araba","araba"),("eşya","eşya"),("diğer","diğer")] )
    start_price = IntegerField("İhalenin Başlangıç Fiyatı",validators=[validators.NumberRange(min=0,max = 999999999)])
    offered_price = IntegerField("İhaleye Teklif Edilen Fiyat",validators=[validators.NumberRange(min=0,max = 999999999)])
    deleted = BooleanField()
    

class KayıtFormu(Form):
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 4,max = 20)])
    email = StringField("Email",validators=[validators.Email(message="Geçerli bir Email adresi girin" )])
    password = PasswordField("Parola",validators=[validators.DataRequired(message="Bir parola belirleyin" ),validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor")])
    confirm = PasswordField("Parola Doğrula")
    admin = BooleanField("Admin")
class GirişFormu(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")
class SilmeFormu(Form):
    delete = BooleanField("Silme Doğrulama")    

app = Flask(__name__)
app.secret_key = "ihale"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ihale_db"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)



@app.route("/")
def anasayfa():
   return render_template("anasayfa.html")

@app.route("/ihaleler")
def ihaleler():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From ihaleler"

    result = cursor.execute(sorgu)

    if result > 0:
        ihaleler = cursor.fetchall()
        return render_template("ihaleler.html",ihaleler = ihaleler)
    else:
        return render_template("ihaleler.html")

@app.route("/register",methods = ["GET","POST"])
def register():
    form = KayıtFormu(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        admin = form.admin.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(email,username,password,admin) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(email,username,password,admin))
        mysql.connection.commit()

        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

@app.route("/dashboard")
@register_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From ihaleler where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        ihaleler = cursor.fetchall()
        return render_template("controlpanel.html",ihaleler = ihaleler)
    else:
        return render_template("controlpanel.html")        

@app.route("/login",methods =["GET","POST"])
def login():
    form = GirişFormu(request.form)
    if request.method == "POST":
       username = form.username.data
       password_entered = form.password.data

       
       cursor = mysql.connection.cursor()

       sorgu1 = "Select * From users where username = %s"

       result = cursor.execute(sorgu1,(username,))

       sorgu2 = "Select admin From users where username = %s"

       result2 = cursor.execute(sorgu2,(username,)) 
      

     

       if result > 0:
           data = cursor.fetchone()
           real_password = data["password"]
          
           if sha256_crypt.verify(password_entered,real_password):
               flash("Başarıyla Giriş Yaptınız","success")
               if result2 == True:
                    session["logged_admin"]  = True 
               session["logged_in"] = True
               session["username"] = username
               

               return redirect(url_for("anasayfa"))
           else:
               flash("Parolanızı Yanlış Girdiniz","danger")
               return redirect(url_for("login")) 

               


       else:
           flash("Böyle bir kullanıcı bulunmuyor","danger")
           return redirect(url_for("login"))

    
    return render_template("login.html",form = form)


@admin_required
@app.route("/addihale",methods = ["GET","POST"])
def addihale():
    form = IhaleFormu(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        end_date = form.content.data
        category = form.content.data
        start_price = form.content.data
        offered_price = form.content.data
        deleted = form.content.data
        


        cursor = mysql.connection.cursor()

        sorgu = "Insert into ihaleler(title,content,end_date,category,start_price,offered_price,deleted) VALUES(%s,%s,%s,%s,%s,%s,%s)"

        cursor.execute(sorgu,(title,content,end_date,category,start_price,offered_price,deleted,session["username"]))

        mysql.connection.commit()

        cursor.close()

        flash("İhale Başarıyla Eklendi","success")

        return redirect(url_for("ihaleler"))

    return render_template("addihale.html",form = form)    

@app.route("/ihale/<string:id>/addoffer",methods = ["GET","POST"])
@register_required
def addoffer(id):
   if request.method == "GET":
       cursor = mysql.connection.cursor()

       sorgu = "Select * from ihaleler where id = %s"
       result = cursor.execute(sorgu,(id,session["username"]))

       if result == 0:
           flash("Böyle bir ihale yok veya bu işleme yetkiniz yok","danger")
           return redirect(url_for("index"))
       else:
           ihale = cursor.fetchone()
           form = IhaleFormu()

           form.offered_price.data = ihale["offered_price"]
           sorgu2 = "Select start_price, offered_price from ihaleler where id = %s "
           cursor.execute(sorgu2)
           prices = cursor.fetchall()
           return render_template("addoffer.html",form = form, prices = prices)

   else:
       
       form = IhaleFormu(request.form)

       newPrice = form.offered_price.data
       
       sorgu2 = "Select start_price, offered_price from ihaleler where id = %s "
       cursor.execute(sorgu)
       prices = cursor.fetchall()

       sorgu3 = "Update ihaleler Set offered_price = %s, where id = %s "

       cursor = mysql.connection.cursor()

       cursor.execute(sorgu3,(newPrice,id))

       mysql.connection.commit()

       flash("Teklif başarıyla verildi","success")

       return redirect(url_for("/ihale/<string:id>"))


@app.route("/ihale/<string:id>")
def ihale(id):
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * from ihaleler where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        ihale = cursor.fetchone()
        return render_template("ihale.html",ihale = ihale)
    else:
        return render_template("ihale.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("anasayfa"))

@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for("anasayfa"))
   else:
       keyword = request.form.get("keyword")

       cursor = mysql.connection.cursor()

       sorgu = "Select * from ihaleler where title like '%" + keyword +"%'"

       result = cursor.execute(sorgu)

       if result == 0:
           flash("Aranan kelimeye uygun ihale bulunamadı","warning")
           return redirect(url_for("ihaleler"))
       else:
           articles = cursor.fetchall()

           return render_template("ihaleler.html",articles = articles)

@app.route("/ihale/<string:id>/delete")
def delete(id):   
    form = SilmeFormu(request.form) 
    delete = form.delete.data 
    cursor = mysql.connection.cursor()
    sorgu = "Update ihaleler Set deleted = %s, where id = %s"
    cursor.execute(sorgu,(delete,id))
    return redirect(url_for("controlpanel"))

class CurrentDateForm(Form):
    currentdate = DateTimeField(
        label='currentdate',
        format='%Y-%m-%d %H:%M'
        
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.currentdate.data:
            self.currentdate.data = datetime.date.now()
    
if __name__ == "__main__":
    app.run(debug=True)
