# 13DTP - Chris

## Run instructions
**Note: It's recommended to use a dedicated [Python environment](#create-a-python-environment) before continuing**

Install the required packages:

```bash
pip install -r requirements.txt
```
Run the app:
```bash
python3 main.py
```
If it's your first time running this app, it will ask if you want to generate a key. This key is used to check whether a user's cookie is valid or not. On entering `y`, it will create a `.env` that stores the key alongside the `main.py`.

<br>

## Contents
- [Run instructions](#run-instructions)
- [Creating a Python environment](#creating-a-python-environment)
- [Configuring the site](#configuring-the-site)
- [Changing admin password](#changing-admin-account-password)
- [Clearing database](#clearing-database)

<br>

## Creating a Python environment:
Using a dedicated Python environment prevents the required packages from conflicting with system packages and makes it easier to remove this app.

Create the env:
```bash
cd /path/to/app/
python3 -m venv .venv
```
Enter Python environment:

**Windows**
```bash
# Command Prompt
.venv\Scripts\activate.bat

# Powershell
.venv\Scripts\Activate.ps1
```

**Linux/MacOS**
```bash
source .venv/bin/activate
```

<br>

## Configuring the site
In [`📄main.py`](main.py), there is a variable called `vars`. This variable configures some settings on the site.

- `site_title` - The name of the app
- `anim_speed` - Global animation speed (in milliseconds)
- `slogan` - The smaller text under the greeting (only appears on homepage)
- `greeting` - The welcome text that only appears on the homepage
- `heading_brand` - The part of the heading that is a different color
- `heading` - The main part of the heading
- `contact_info` - Copyright stuff at the bottom of the page

The styling of the site can also be changed through [`🎨style.css`](/static/style.css) and by changing the images in [`📁images`](/static/images/)

<br>

## Changing Admin account password
Changing the primary admin password requires access to the terminal that the app is running on. 

1. Enter the login page on the site and enter `Admin` as the username
2. Enter `ResetAdmin` as the password and login
3. Check the terminal and copy and paste the password into the password field on the page
4. Enter new admin password into the terminal and the password should be updated

**Note: While changing password, the site may appear frozen**\

<br>

## Clearing database
The [`💿sites.db`](/instance/sites.db) cannot be empty or missing. If it was, the app would not run due to it being unable to create the foreign keys and the database missing the required data

If you want to clear the database, delete `site.db` and rename `clear.db` to `site.db`

If you want an entirely new database, please ensure the following are in their respective tables

**accounts** (Note: Use [`📄passgen.py`](/passgen.py) to generate new password)
| ID | username | password | email | group |
| --- | --- | --- | --- | --- |
| 1 | Admin | Any | Any | 1 |

**folders** (`url` is generated, use `"/" \|\| ID`)
| ID | owner | name | url | icon | admin | logged_in | private | group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | *NULL* | Folder | {GENERATED} |  | 0 | 0 | 0 |  |

**groups**
| ID | name | can_edit | is_admin |
| --- | --- | --- | --- |
| 1 | admins | 1 | 1 |
| 2 | users | 1 | 0 |

**sites** 
| ID | owner | name | url | folder | description | icon | admin | logged_in |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |  |  |

