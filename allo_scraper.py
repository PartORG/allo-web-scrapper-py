import os

from itertools import product
from bs4 import BeautifulSoup
import time
import pandas as pd 
import csv

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sqlite3
from sqlite3 import Error

def create_connection(db_file=''):
	""" create a database connection to the SQLite database
	    specified by db_file
	:param db_file: database file
	:return: Connection object or None
	"""
	conn = None
	try:
		conn = sqlite3.connect(db_file)
		# create table
		sql_create_projects_table = """ CREATE TABLE IF NOT EXISTS projects (
		                                    id integer PRIMARY KEY,
		                                    word text NOT NULL,
		                                    suggestions text); """
		if conn is not None:
			# create projects table
			create_table(conn, sql_create_projects_table)

	except Error as e:
		print(e)

	return conn

def create_table(conn, create_table_sql):
	""" create a table from the create_table_sql statement
	:param conn: Connection object
	:param create_table_sql: a CREATE TABLE statement
	"""
	try:
		c = conn.cursor()
		c.execute(create_table_sql)
	except Error as e:
		print(e)		

def create_project(conn, project):
	"""
	Create a new project into the projects table
	:param conn:
	:param project:
	:return: project id
	"""
	sql = ''' INSERT INTO projects(word,suggestions)
	          VALUES(?,?) '''
	cur = conn.cursor()
	cur.execute(sql, project)
	conn.commit()

def select_last_id(conn):
    """
    Query last inserted data in projects table - max(id)
    :param conn: the Connection object
    :return: value for max(id)
    """
    cur = conn.cursor()
    cur.execute("SELECT max(id) FROM projects")
    conn.commit()
    rows = cur.fetchall()
    return rows

def letter_combinations():
	"""
    Creates all combinations of 1,2 and 3 letters
    for searching word
    return: list of all combinations
    """
	alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
	# print(len(alphabet))
	keywords_2 = [a+b for a,b in product(alphabet, repeat=2)]
	keywords_3 = [a+b+c for a,b,c in product(alphabet, repeat=3)]

	all_combinations = alphabet + keywords_2 + keywords_3
	# print(len(all_together))
	return all_combinations

if __name__ == '__main__':
	# initialization
	currentDirectory = os.getcwd()
	conn = create_connection(currentDirectory + '\\allo_database.db')
	driver = webdriver.Chrome(currentDirectory +"\\chromedriver.exe")
	# webpage to scrap data from
	driver.get("https://allo.ua/")
	# preparing page - wait till it is completely loaded
	try:
	    element = WebDriverWait(driver, 20).until(
	        EC.presence_of_element_located((By.XPATH, '//*[@id="header-mega-menu"]/div[1]/div/div[1]/div[1]/div/div[1]/div[2]/i'))
	    )
	except:
		print('Page not ready ((')
		driver.quit()
		quit()

	time.sleep(4)
	print("Page is ready!")

	# find search form input element on web page
	element_form = driver.find_element_by_xpath('//*[@id="header-mega-menu"]/div[1]/div/div/div[3]/div/ul/li[4]/div/div/form')
	element_form_input = element_form.find_element_by_xpath('//*[@id="search-form__input"]')

	# check if script already processed some words from combinations list
	# start at the beginning if it is a first run of script
	start = 0
	last = list(select_last_id(conn)[0])
	if last[0] != None:
		start = int(last[0])

	# get combinations
	all_together = letter_combinations()
	print('\nYou can stop script execution by pressing CTRL + C.\n')
	try:
		# main scrapping loop
		for x in range(start, len(all_together)):
			# send word to searching input form on webpage
			element_form_input.click()
			element_form_input.send_keys(str(all_together[x]))
			
			time.sleep(2)
			try:
				# find element with suggestions
				data_suggestion = driver.find_element_by_xpath('//*[@id="header-mega-menu"]/div[1]/div/div/div[3]/div/ul/li[4]/div/div[2]/div/div[1]/ul[1]')
				data_text = ', '.join(data_suggestion.text.split('\n'))
				element_form_input.clear()
				#insert into database:
				project = (all_together[x], data_text);
				create_project(conn, project)
			except:
				# incase empty pop-up suggestion box on webpage
				element_form_input.clear()
				#insert into database:
				project = (all_together[x], 'No suggestions found for - ' + str(all_together[x]));
				create_project(conn, project)

			time.sleep(1)

	except KeyboardInterrupt:
		# after pressing CTRL + C 
		print("KeyboardInterrupt has been caught and script stopped.")

	# in the end - close all connections
	conn.close()
	driver.quit()
	print('End of execution. Connection closed and driver closed.')