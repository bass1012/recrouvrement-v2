from app import create_app, db
from app.models import User

app = create_app('development')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created!")
    app.run(debug=True)
