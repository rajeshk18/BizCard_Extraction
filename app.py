import os
import re
from PIL import Image
import cv2
import easyocr
import matplotlib.pyplot as plt
import mysql.connector as sql
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

# Page setup
icon = Image.open("icon.png")
st.set_page_config(page_title= "BizCardX: Extracting Business Card Data with OCR",
                   page_icon= icon,
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# Tool built on OCR, Streamlit GUI, SQL, Data Extraction """})
st.markdown("<h1 style='text-align: center; color: white;'>BizCardX: Extracting Business Card Data with OCR</h1>", unsafe_allow_html=True)

def set_background():
    st.markdown(f""" 
                    <style>.stApp {{
                            background: url("https://r4.wallpaperflare.com/wallpaper/807/752/52/abstract-minimalistic-hexagons-textures-artwork-honeycomb-1920x1080-abstract-textures-hd-art-wallpaper-79f0083d216a6d0b7627481f30b1562d.jpg");
                            background-size: cover}}
                    </style>
                """
                ,unsafe_allow_html=True) 
    
set_background()

# Top Menu
selected = option_menu(None, ["Upload & Extract","Edit"], 
                       icons=["cloud-upload","pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "27px", "text-align": "centre", "margin": "0px", "--hover-color": "#9370DB"},
                               "icon": {"font-size": "27px"},
                               "container" : {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#800080"}})

# EasyOCR Reader : Initialize
reader = easyocr.Reader(['en'])

# DB Connection
mydb = sql.connect(host="localhost",
                   user="root",
                   password="Olivia837*#&",
                   database= "bizcardx"
                  )
mycursor = mydb.cursor(buffered=True)

# TABLE CREATION
mycursor.execute('''CREATE TABLE IF NOT EXISTS bizcard_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )''')

# UPLOAD AND EXTRACT MENU
if selected == "Upload & Extract":
    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader("upload here",label_visibility="collapsed",type=["png","jpeg","jpg"])
        
    if uploaded_card is not None:
        
        def save_card(uploaded_card):
            with open(os.path.join("uploaded_cards",uploaded_card.name), "wb") as f:
                f.write(uploaded_card.getbuffer())   
        save_card(uploaded_card)
        
        def image_preview(image,res): 
            for (bbox, text, prob) in res: 
              # unpack the bounding box
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15,15)
            plt.axis('off')
            plt.imshow(image)
        
        # Original Bizcard
        col1,col2 = st.columns(2,gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("### Uploaded the card")
            st.image(uploaded_card)
        # Data to be extracted highlight... 
        with col2:
            st.markdown("#     ")
            st.markdown("#     ")
            with st.spinner("Please wait processing image..."):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("### Card Processed and Data Extracted")
                st.pyplot(image_preview(image,res))  
                
            
        #easy OCR
        saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
        result = reader.readtext(saved_img, detail = 0, paragraph=False)

        #st.write(result)
        
        # Convert image to binary and store in DB
        def img_to_binary(file):
            with open(file, 'rb') as file:
                binaryData = file.read()
            return binaryData
        
        data = {"company_name" : [],
                "card_holder" : [],
                "designation" : [],
                "mobile_number" :[],
                "email" : [],
                "website" : [],
                "area" : [],
                "city" : [],
                "state" : [],
                "pin_code" : [],
                "image" : img_to_binary(saved_img)
               }

        def get_data(res):
            for ind,i in enumerate(res):

                # Read site URL
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)

                # Read EmailID
                elif "@" in i:
                    data["email"].append(i)

                # Read Mobile
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) ==2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                # Read Company Name
                elif ind == 0:
                    data["company_name"].append(i)

                # Read Card Holder Name
                elif ind == 1:
                    data["card_holder"].append(i)

                # Read designation
                elif ind == 2:
                    data["designation"].append(i)

                # Read Address
                #if re.findall('^[0-9].+, [a-zA-Z]+',i):
                #    data["area"].append(i.split(',')[0])
                #elif re.findall('[0-9] [a-zA-Z]+',i):
                #    data["area"].append(i)
                if "#" in i:
                    data["area"].append(i + ',' + res[ind+1])

                # Read State
                #state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                #if state_match:
                #     data["state"].append(i[:9])
                #elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                #    data["state"].append(i.split()[-1])
                #else:
                #    data["state"].append("No State")

                #if len(data["state"]) == 2:
                #    data["state"].pop(0)

                # Read Pin Code
                preval = i
                if len(i)>=6 and i.isdigit():
                    data["pin_code"].append(i)
                    data["state"].append(res[ind-1])
                    data["city"].append(res[ind-2])
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["pin_code"].append(i[10:])
                    data["state"].append(res[ind-1])
                    data["city"].append(res[ind-2])
       
        get_data(result)

        st.success("### Data Extracted!")
        #st.write(data)
        df = pd.DataFrame(data)
        st.write(df)
        
        if st.button("Upload to Database"):
            for i,row in df.iterrows():
                #here %S means string values 
                sql = """INSERT INTO bizcard_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                mycursor.execute(sql, tuple(row))
                # the connection is not auto committed by default, so we must commit to save our changes
                mydb.commit()
            st.success("#### Uploaded to database successfully!")
        
# EDIT MENU    
if selected == "Edit":
    col1,col2,col3 = st.columns([3,3,2])
    col2.markdown("## Edit / Delete the Card")
    column1,column2 = st.columns(2,gap="large")
    try:
        with column1:
            mycursor.execute("SELECT card_holder FROM bizcard_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")
            mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from bizcard_data WHERE card_holder=%s",
                            (selected_card,))
            result = mycursor.fetchone()

            company_name = st.text_input("Company_Name", result[0])
            card_holder = st.text_input("Card_Holder", result[1])
            designation = st.text_input("Designation", result[2])
            mobile_number = st.text_input("Mobile_Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pin_Code", result[9])

            if st.button("Save"):
                mycursor.execute("""UPDATE bizcard_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
                mydb.commit()
                st.success("Saved successfully.")

        with column2:
            mycursor.execute("SELECT card_holder FROM bizcard_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            if st.button("Yes Delete Business Card"):
                mycursor.execute(f"DELETE FROM bizcard_data WHERE card_holder='{selected_card}'")
                mydb.commit()
                st.success("Card has been deleted successfully.")
    except:
        st.warning("There is no data available in the database")
    
    if st.button("View updated data"):
        mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from bizcard_data")
        updated_df = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
        st.write(updated_df)
