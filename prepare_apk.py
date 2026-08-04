import os

def prepare_apk_files():
    # 1. Pasajero
    if os.path.exists('frontend_passenger/index.html'):
        with open('frontend_passenger/index.html', 'r', encoding='utf-8') as f:
            pass_html = f.read()
        
        pass_html_apk = pass_html.replace("fetch('/api/", "fetch('https://apptrnasportesaltos.onrender.com/api/")
        pass_html_apk = pass_html_apk.replace('href="/driver/"', 'href="https://apptrnasportesaltos.onrender.com/driver/"')
        pass_html_apk = pass_html_apk.replace('href="/dashboard/"', 'href="https://apptrnasportesaltos.onrender.com/dashboard/"')
        pass_html_apk = pass_html_apk.replace('href="/manifest_passenger.json"', '')

        os.makedirs('android_pasajero/www', exist_ok=True)
        with open('android_pasajero/www/index.html', 'w', encoding='utf-8') as f:
            f.write(pass_html_apk)
        print("[OK] android_pasajero/www/index.html listo.")

    # 2. Conductor
    if os.path.exists('frontend_driver/index.html'):
        with open('frontend_driver/index.html', 'r', encoding='utf-8') as f:
            drv_html = f.read()

        drv_html_apk = drv_html.replace("fetch('/api/", "fetch('https://apptrnasportesaltos.onrender.com/api/")
        drv_html_apk = drv_html_apk.replace('href="/dashboard/"', 'href="https://apptrnasportesaltos.onrender.com/dashboard/"')
        drv_html_apk = drv_html_apk.replace('href="/manifest_driver.json"', '')

        os.makedirs('android_conductor/www', exist_ok=True)
        with open('android_conductor/www/index.html', 'w', encoding='utf-8') as f:
            f.write(drv_html_apk)
        print("[OK] android_conductor/www/index.html listo.")

if __name__ == '__main__':
    prepare_apk_files()
