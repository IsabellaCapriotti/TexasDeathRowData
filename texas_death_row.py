import urllib.request, urllib.parse, urllib.error
import sqlite3
import re
from bs4 import BeautifulSoup

#**********************************************************************
# INITIAL DATA LOAD
#**********************************************************************
def loadData():
    #Form BeautifulSoup object from website
    soup = BeautifulSoup(urllib.request.urlopen('https://www.tdcj.texas.gov/death_row/dr_executed_offenders.html').read().decode(), 'html.parser')

    #Get original table from document
    mainDataTable = soup.find(title='Table showing list of executed offenders')

    data = mainDataTable.find_all('tr')

    #Database setup
    conn = sqlite3.connect('texas_death_row.sqlite')
    cur = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS TEXAS_DEATH_ROW')
    cur.execute('''
    CREATE TABLE TEXAS_DEATH_ROW(
        ID INTEGER UNIQUE NOT NULL,
        INCIDENT_SUMMARY VARCHAR(1000),
        LAST_STATEMENT VARCHAR(1000), 
        LAST_NAME VARCHAR(30),
        FIRST_NAME VARCHAR(30),
        AGE INTEGER,
        DATE VARCHAR(10),
        RACE VARCHAR(20),
        PRIMARY KEY(ID)
    )
    ''')

    #Clear debug file
    fileHandle = open('death_row_debug.txt', 'x', encoding='utf-8')
    fileHandle.write("")
    fileHandle.close()   

    #Set up debug file
    fileHandle = open('death_row_debug.txt', 'a', encoding='utf-8')

    #Iterate through rows, load into database
    #(Skip first header row)
    for row in data[1:]:

        items = row.find_all('td')
        
        #Skip empty rows
        if len(items) < 1:
            continue

        #GET INFORMATION

        #ID
        id = items[0].get_text()

        #Incident summary
        sumLink = items[1].find('a')['href']
        try:
            crimeDetailsPage = BeautifulSoup(urllib.request.urlopen('https://www.tdcj.texas.gov/death_row/' + sumLink).read().decode(), 'html.parser')
            
            incident_summary = crimeDetailsPage.find('span', string='Summary of Incident')

            if incident_summary is None:
                incident_summary = 'NULL'
            else:
                incident_summary = incident_summary.find_parent().get_text()[20:].strip()
        except:
            incident_summary = 'NULL'
            fileHandle.write('Could not load incident summary for ' + str(id) + '\n')

        
        #Last statement
        statementLink = items[2].find('a')['href']
        try:
            #Find statement header
            statementPage = BeautifulSoup(urllib.request.urlopen('https://www.tdcj.texas.gov/death_row/' + statementLink).read().decode(), 'html.parser')
            statementText = statementPage.find(class_='bold', string=re.compile(".*Last Statement.*"))

            #Get text of last statement
            if statementText is None:
                last_statement = 'NULL'
            else:
                last_statement_list = [item.get_text().strip() for item in statementText.find_all_next('p')]
                last_statement = ""
                #Convert to one big string
                for item in last_statement_list:
                    last_statement = last_statement + item + ' '
            
        except:
            last_statement = 'NULL'
            fileHandle.write('Could not load final statement for ' + str(id) + '\n')


        #First name + last name
        last_name = items[3].get_text().strip()
        first_name = items[4].get_text().strip()

        #Age
        age = items[6].get_text().strip()

        #Date
        exec_date = items[7].get_text().strip()
        
        #Race
        race = items[8].get_text().strip()

        #Write to debug file
        fileHandle.write('Id: ' + str(id) + ' Incident Summary: ' + str(incident_summary) + ' Last Statement: ' + str(last_statement) + ' First Name: ' + first_name + ' Last name: ' + last_name + ' Age: ' + str(age) + ' Date: ' + str(exec_date) + ' Race: ' + race + '\n\n')

        #LOAD INTO DATABASE
        cur.execute('''
            INSERT INTO TEXAS_DEATH_ROW
            VALUES
            (?,?,?,?,?,?,?,?)
        ''', (id, incident_summary, last_statement, last_name, first_name, age, exec_date, race))

        conn.commit()
        print(str(id))

    #Close debug file
    fileHandle.close()


#**********************************************************************
# QUERYING
#**********************************************************************
con = sqlite3.connect('texas_death_row.sqlite')
cur = con.cursor()

def getRandom():

    #Get random entry
    cur.execute('''
        SELECT * FROM TEXAS_DEATH_ROW
        ORDER BY RANDOM()
        LIMIT 1
    ''')

    #Fetch + print results
    res = cur.fetchall()

    for row in res:
        print('Id: ' + str(row[0]))
        print('Name: ' + str(row[4]) + ' ' + str(row[3]))
        print('Age: ' + str(row[5]))
        print('Date: ' + str(row[6]))
        print('Race: ' + str(row[7]))
        print('Incident Summary: ' + str(row[1]))
        print('Last Statement: ' + str(row[2]))


loadData()
getRandom()