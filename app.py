from selenium import webdriver
from chromedriver_py import binary_path
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import json
import re
import pandas as pd


def writejson(filename,data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def readjson(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)



# Chrome WebDriver'ı başlatın
svc = webdriver.ChromeService(executable_path=binary_path)
driver = webdriver.Chrome(service=svc)

# Bir web sayfasını açın
driver.get("https://www.decathlon.com.tr")

time.sleep(5)
  


def linkleri_cek():
    link_listesi = {}
    sayac = 0
    urunsayisi=0
    for i in range(1,122):
        driver.get(f"https://www.decathlon.com.tr/tum-urunler?from={urunsayisi}&size=40")
        urunsayisi=urunsayisi+40
        time.sleep(3)
        baslık = driver.find_elements(By.CLASS_NAME, "dpb-product-model-link")
        for element in baslık:
            sayac=sayac+1
            link_listesi[f'link_{sayac}'] = element.get_attribute("href")
            print(f"{sayac} - {element.get_attribute("href")}")
            

    writejson('linkler.json',link_listesi)



def linklerden_veri_cek():
    sayac = 0
    urun_jsonları = readjson('linkler.json')
    urun_dict = {}
    
    for key, value in urun_jsonları.items():
        sayac += 1
        driver.get(f"{value}")
        print(f"{sayac} - {value}")
        
        try:
            urun_adı = driver.find_element(By.CLASS_NAME, "product-name")
            marka = driver.find_element(By.CSS_SELECTOR, "#app > main > article > div.vtmn-relative.vtmn-z-\[2\] > section > a")
            kategori = driver.find_element(By.CLASS_NAME, "vtmn-breadcrumb")
            link = driver.current_url
            kategori_link = driver.find_elements(By.CLASS_NAME, "breadcrumb-link")
            kategori_link_son = kategori_link[-1].get_attribute("href")
            aciklama = driver.find_element(By.CSS_SELECTOR, "#app > main > article > div.vtmn-relative.vtmn-z-\[2\] > section > p.vtmn-text-base.vtmn-mt-2").text
            aciklama2 = driver.find_element(By.CSS_SELECTOR, "#app > main > article > div.vtmn-relative.vtmn-z-\[2\] > section > p.vtmn-text-base.vtmn-mb-0").text
            teknik_bilgiler = driver.find_element(By.CSS_SELECTOR, "#ProductFunctionalities-8898de662bbe615edc8d3982473eeb394d01021f").text
            varyant_ozet = aciklama + aciklama2 + teknik_bilgiler
            varyant_ozet = re.sub(r'\s+', ' ', varyant_ozet)
            
            try:
                varyant_dahafazla_btn = driver.find_element(By.CSS_SELECTOR, "#app > main > article > div.vtmn-relative.vtmn-z-\[2\] > section > section > ul > li:nth-child(5) > button")
                varyant_dahafazla_btn.click()
            except:
                pass
            
       
            urun_bilesimi = driver.find_element(By.CSS_SELECTOR, "#ProductConception-04eaa7a931d4096311b4bdf94f4cb34ea90b3902 > div > div > div > div:nth-child(1) > div").text
            varyant_kodları = driver.find_elements(By.CLASS_NAME, "variant-list__button")
            varyantlar = []
            
            index = 1
            for varyant in varyant_kodları:
                if index == 5:
                    index+=1
                    continue
                varyant.click()
                time.sleep(0.2)
                try:
                    varyant_fiyatı = driver.find_element(By.CLASS_NAME, "vtmn-price").text
                    index += 1
                except:
                    varyant_fiyatı = "Fiyat bulunamadı"
                
                eve_teslimat = ""
                try:
                    eve_teslimat = driver.find_element(By.CSS_SELECTOR,"#app > main > article > div.vtmn-relative.vtmn-z-\[2\] > section > div.vtmn-text-base.online-availability.vtmn-mt-5.svelte-ph6b92 > div > span.vtmn-text-content-primary").text
                except:
                    pass
                varyant_adi = driver.find_element(By.CLASS_NAME, "product-name").text
                cinsiyet=""
                if "erkek" in varyant_adi.lower():
                    cinsiyet = "erkek"
                elif "kadın" in varyant_adi.lower():
                    cinsiyet = "kadın"
                varyant_id = varyant.get_attribute("data-id")
                varyant_rengi = varyant.get_attribute("title")
                varyant_secenekleri = driver.find_elements(By.XPATH, "/html/body/div[2]/main/article/div[2]/section/div[3]/div[2]/ul/li")
                varyant_image = driver.find_elements(By.XPATH, "/html/body/div[2]/main/article/div[1]/div/div/ul/li/button/img")
               
                varyantlar.append({
                    "varyant_adi":varyant_adi,
                    "varyant_kodu": varyant_id,
                    "varyant_rengi": varyant_rengi,
                    "eve_teslimat": eve_teslimat,
                    "varyant_cinsiyet": cinsiyet,
                    "varyant_fiyatı": varyant_fiyatı,
                    "varyant_seceneği": [secenek.get_attribute("innerText") for secenek in varyant_secenekleri],
                    "varyant_ana_image": varyant_image[0].get_attribute("src").split("?")[0],
                    "varyant_images": [image.get_attribute("src").split("?")[0] for image in varyant_image]
                })
            
            urun_dict[f"{driver.current_url}"] = {
                "urun_adı": urun_adı.text,
                "marka": marka.text,
                "kategori": kategori.text,
                "link": link,
                "kategori_link": kategori_link_son,
                "varyantlar": varyantlar,
                "varyant_ozet": varyant_ozet,
                "urun_bilesimi": urun_bilesimi,
                
            }
        
        except Exception as e:
            print(e)
            urun_dict[f"{driver.current_url}"] = "bulunamadı"
            continue
       
        
    writejson("urunler_ozellikler3.json",urun_dict)


def excele_yazdır():
    data_list = []
    json_data = readjson("urunler_ozellikler3.json")
    
    for url, data in json_data.items():
        # Eğer data bir string ise, bunu atla
        if isinstance(data, str):
            continue  # Bu veri işlenemiyorsa atla
        
        # Devamında, artık data'nın bir dict olduğunu varsayabiliriz
        marka = data.get("marka", "")
        kategori = data.get("kategori", "")
        ozet = data.get("varyant_ozet", "")
        urun_bilesimi = data.get("urun_bilesimi", "")
        
        # "Teknik Bilgiler" kısmını "varyant_ozet" içinden ayırma
        teknik_bilgiler = ""
        if "Teknik Bilgiler" in ozet:
            teknik_bilgiler = ozet.split("Teknik Bilgiler", 1)[1].strip()
        
        # Özeti 500 karakterle sınırla
        ozet_limited = ozet[:500].strip()
        
        for varyant in data["varyantlar"]:
            Stok_durumu = varyant.get("Stok_durumu", "").strip()
            # Eğer varyant seçeneği varsa her biri için ayrı satır oluşturulur
            varyant_seceneği = varyant.get("varyant_seceneği", [""])  # Eğer varyant seçeneği yoksa boş bir liste döner
            for secenek in varyant_seceneği:
                varyant_data = {
                    "kategori adı": kategori.split("\n")[-1],  # Kategorinin son kısmını alıyoruz
                    "ürün linki": url,
                    "marka": marka,
                    "Ürün kategorisi": kategori,
                    "ürün varyant adı": varyant["varyant_adi"],
                    "Beden(varyant Seçeneği)": secenek,
                    
                    "ürün varyant kodu": varyant["varyant_kodu"],
                    "fiyat": varyant["varyant_fiyatı"],
                    "ürün ana fotosu": varyant["varyant_ana_image"],
                    "ürün ek foto": ", ".join(varyant["varyant_images"]),
                    "ÖZET": ozet_limited,
                    "renk": varyant["varyant_rengi"],
                    "Teknik Bilgiler": teknik_bilgiler,
                    
                    "Cinsiyet": varyant.get("varyant_cinsiyet", ""),
                    "Ürün Bileşimi": urun_bilesimi
                }
                
                data_list.append(varyant_data)

    # DataFrame oluşturma
    df = pd.DataFrame(data_list)
    print(df.head())  # DataFrame'in ilk birkaç satırını kontrol etmek için
    # Excel dosyasına kaydetme
    excel_file_path = 'dec_output.xlsx'
    df.to_excel(excel_file_path, index=False)

#linklerden_veri_cek()
excele_yazdır()


driver.quit()