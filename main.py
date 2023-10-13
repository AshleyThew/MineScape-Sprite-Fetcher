
from tkinter import simpledialog, messagebox, Tk, Label, Button, filedialog, END, Toplevel, WORD, Text, DISABLED
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageTk
import re, io, os, requests

import json

# Dictionary to store last used locations for different file types
last_used_locations = {
    "png": "",
    "json": "",
}

# Load last used locations from a configuration file
def load_last_used_locations():
    try:
        with open("last_saved_locations.json", "r") as file:
            data = json.load(file)
            last_used_locations.update(data)
    except FileNotFoundError:
        pass

# Save last used locations to a configuration file
def save_last_used_locations():
    with open("last_saved_locations.json", "w") as file:
        json.dump(last_used_locations, file)

def save_as_file(file_type):
    file_path = filedialog.asksaveasfilename(
        filetypes=[(f"{file_type.upper()} Files", f"*.{file_type}")],
        initialdir=last_used_locations.get(file_type, ""),
    )
    if file_path:
        # Update the last used location for the file type
        last_used_locations[file_type] = file_path
        # Save the file

global items
items = []

def add_item(item):
    global items
    items.append(item)

def get_infobox_buttons(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the div element with class 'infobox-buttons'
        infobox_buttons = soup.find('div', class_='infobox-buttons')
        
        data_switch_anchor_list = []
        
        if infobox_buttons:
            # Find all 'span' elements within the 'div' with class 'infobox-buttons'
            span_children = infobox_buttons.find_all('span')
            
            # Extract the 'data-switch-anchor' attribute from each 'span'
            data_switch_anchor_list = [span.get('data-switch-anchor') for span in span_children if 'data-switch-anchor' in span.attrs]
        
        return data_switch_anchor_list
    except requests.exceptions.RequestException as e:
        return None

def load_page(url):
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(5)
    try:
        # Use Selenium to open the webpage
        driver.get(url)

        element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "infobox-image"))
        )
    except Exception as e:
        a=1
    return driver

def get_infobox(url, length):
    driver = None
    if length > 1:
        driver = load_page(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    else:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

    # Find all td elements with class 'infobox-image'
    td_tags = soup.find_all('td', class_='infobox-image')

    # Find all td elements with class 'infobox-image'
    th = soup.find('th', class_='infobox-header')

    img_urls = []
    names = []

    for td in td_tags:
        img_tag = td.find('img')
        if img_tag and 'src' in img_tag.attrs:
            img_urls.append(img_tag['src'])
            names.append(th.text.upper().replace(" ", "_").replace("(", "_").replace(")", "").replace("__", "_").replace("'", ""))

    # Close the Selenium driver
    if driver:
        driver.quit()
    return [img_urls, names]

def display_images(images):
    root = Tk()
    root.title("Select an Image")

    selected_image = None

    def select_image(image_url, index):
        nonlocal selected_image
        selected_image = [image_url, index]
        root.destroy()

    col = 0

    for index, image_url in enumerate(images):
        response = requests.get('https://oldschool.runescape.wiki/'+image_url)
        if response.status_code == 200:
            img_data = io.BytesIO(response.content)
            img = Image.open(img_data)
            # img = img.resize((150, 150), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(img)

            label = Label(root, image=img)
            label.image = img  # Keep a reference
            label.grid(row=0, column=col)

            select_button = Button(root, text="Select", command=lambda url=image_url, select=index: select_image(url,select))
            select_button.grid(row=1, column=col)
            col+=1

        # Center the custom dialog
    root.geometry(f"+{root.winfo_screenwidth() // 2 - root.winfo_reqwidth() // 2}+{root.winfo_screenheight() // 2 - root.winfo_reqheight() // 2}")

    root.mainloop()
    return selected_image

def download_and_save_image(image_url, lower_name, max_size=(32, 32)):
    # Download the image from the URL
    response = requests.get(image_url)
    if response.status_code == 200:
        # Ask the user for a file path to save the image
        file_path = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            initialdir=os.path.dirname(last_used_locations.get("png", "")),
            initialfile=lower_name)

        if 'ms/models' not in file_path:
            messagebox.showerror("Error", "Please save to 'ms/models/*'")
            return None

        if file_path:
            last_used_locations['png'] = file_path
            save_last_used_locations()
            # Open the image from the response content
            img = Image.open(io.BytesIO(response.content))

            # Check if the image size is larger than max_size
            if img.size[0] < max_size[0] or img.size[1] < max_size[1]:
                # Resize the image to max_size
                # Create a blank 32x32 image
                new_img = Image.new("RGBA", max_size, (0, 0, 0, 0))

                # Calculate the position to paste the original image in the center
                x = (max_size[0] - img.width) // 2
                y = (max_size[1] - img.height) // 2

                # Paste the original image onto the new image
                new_img.paste(img, (x, y))
                img = new_img

            # Save the new image to the chosen file path, overwriting if necessary
            img.save(file_path, "PNG")
            return file_path
        else:
            messagebox.showerror("Error", "No file selected.")
    else:
       messagebox.showerror("Error", "Failed to download the image.")
    
    return None

def open_save_item(path, upper_name):
    file_path = filedialog.askopenfilename(
        title=f"Save To Model JSON...",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        initialdir=os.path.dirname(last_used_locations.get("json", "")),
        )
        
    if file_path:
        last_used_locations['json'] = file_path
        save_last_used_locations()
        # Read the file content
        with open(file_path, 'r') as file:
            lines = file.readlines()

        replaced = False

        # Find and replace the first line with "item/empty"
        for i, line in enumerate(lines):
            if "item/empty" in line:
                # Define a regular expression to extract the custom_model_data value
                custom_model_data_pattern = r'"custom_model_data":(\d+)'

                # Use the regular expression to extract the custom_model_data value
                custom_model_data_match = re.search(custom_model_data_pattern, line)

                # Extract the custom_model_data value if a match is found
                if custom_model_data_match:
                    custom_model_data = custom_model_data_match.group(1)
                    lines[i] = line.replace("item/empty", "ms:" + path)
                    replaced = True
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    add_item(upper_name + '\t' + filename + '\t' + custom_model_data)
                    break

        if replaced:
            # Write the modified content back to the file
            with open(file_path, 'w') as file:
                file.writelines(lines)
        else:
            messagebox.showerror("Error", "'item/empty' not found in file.")
    else:
        messagebox.showerror("Error", "No file selected.")


def open_again():
    custom_dialog = Tk()
    custom_dialog.title("Items")

    def close():
        custom_dialog.destroy()

    def okay():
        custom_dialog.destroy()
        main()

    # Create a text widget (textbox) with read-only state
    text_widget = Text(custom_dialog, wrap=WORD, height=10, width=40)
    text_widget.pack()
    global items
    text_widget.insert(END, '\n'.join(items))

    # Make the text widget read-only
    text_widget.config(state=DISABLED)

    ok_button = Button(custom_dialog, text="Again", command=okay)
    ok_button.pack()

    ok_button = Button(custom_dialog, text="Close", command=close)
    ok_button.pack()

    # Center the custom dialog
    custom_dialog.geometry(f"+{custom_dialog.winfo_screenwidth() // 2 - custom_dialog.winfo_reqwidth() // 2}+{custom_dialog.winfo_screenheight() // 2 - custom_dialog.winfo_reqheight() // 2}")

    # Display the custom dialog as a modal dialog
    # custom_dialog.transient(root)
    custom_dialog.grab_set()
    custom_dialog.focus_set()
    # Start the Tkinter main loop
    custom_dialog.mainloop()

# Main GUI function
def main():
    global img_src_list

    url = simpledialog.askstring("Input", "Enter URL:")
    if url and url.startswith("https://oldschool.runescape.wiki/w/"):
        # Remove the # and everything after it
        if "#" in url:
            url = url.split("#")[0]
        buttons = get_infobox_buttons(url)
        img_src_list = []  # List to accumulate infobox images
        names = []
        if buttons:
            for anchor in buttons:
                infobox = get_infobox(url + anchor, len(buttons))
                imgs = infobox[0]
                if imgs:
                    img_src_list.extend(imgs)
                    names.extend(infobox[1])
        else:
            infobox = get_infobox(url, 1)
            img_src_list.extend(infobox[0])
            names.extend(infobox[1])

        if img_src_list:
            selected = display_images(img_src_list)
            if selected:
                name = names[selected[1]]
                saved = download_and_save_image('https://oldschool.runescape.wiki/' + selected[0], name.lower())
                if saved:
                    path = saved.split("ms/models/")[1]
                    open_save_item(path, name)
            else:
                messagebox.showerror("Error", "No images selected.")
        else:
            messagebox.showerror("Error", "No images found on the page.")
    else:
        messagebox.showerror("Error", "Invalid URL. URL should start with 'https://oldschool.runescape.wiki/w/'")
    
    open_again()


if __name__ == "__main__":
    load_last_used_locations()
    main()