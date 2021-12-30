from interfaces import bot
from views import console
from models.vocabulary import Vocabulary
from models.from_cambridge import FromCambridge
from models.from_bookmarks import FromBookmarks
from models.google_spread_sheet import GoogleSpreadSheet
from models.own_example_sentence import OwnExampleSentence
from models.csv import CSV
import helper



class InputVocabularyBot(bot.Bot):
    def __init__(self, config: dict, speak_color='green'):
        super().__init__(speak_color)
        self.config = config
        self.bookmarks_file_path = config['FILES']['DIR'] + config['FILES']['BOOKMARKS_FILE_NAME'] 
        self.examples_file_path = config['FILES']['DIR'] + config['FILES']['EXAMPLES_FILE_NAME'] 
        self.csv_file_path = config['FILES']['DIR'] + config['FILES']['CSV_FILE_NAME'] 
        self.is_GSS = False
        self.is_CSV = False
        self.GSS = None
        self.CSV = None
        self.vocabulary = None
        self.scraping = None
        self.url = None
        self.examples = None
        self.result = {'scraping': [],
                        'voc_written': [],
                        'voc_not_written': [],
                        'ex_written': [],
                        'ex_not_written': []}


    def check_files(self):
        ''' '''
        # Check whether there is a bookmarks file or not. If there is no, tell to copy a bookmarks file until executing
        if helper.is_file(self.bookmarks_file_path):
            template = console.get_template('confirm_to_update_bookmarks.txt', self.speak_color)
            input(template.substitute({
                'USER': '$USER',
                'bookmarks_file_path': self.bookmarks_file_path
                }))
        else:
            while True:
                template = console.get_template('copy_bookmarks.txt', self.speak_color)
                is_quit = input(template.substitute({
                    'USER': '$USER',
                    'bookmarks_file_path': self.bookmarks_file_path
                    }))
                    
                if helper.is_file(self.bookmarks_file_path):
                    break
                if is_quit == 'quit':
                    quit()
        
        # Check whether there is example, csv file or not. If there is no, create those files
        for file_path in [self.examples_file_path, self.csv_file_path]:
            if not helper.is_file(file_path):
                helper.create_file(file_path)
                template = console.get_template('create_file.txt', self.speak_color)
                print(template.substitute({
                    'file_path': file_path,
                    'dir': self.config['FILES']['DIR']
                }))

        return None


    def ask_user_favorites(self):
        ''' '''
        # Ask you want to write vocabularies on GSS
        while True:
            template = console.get_template('ask_favorite.txt', self.speak_color)
            is_yes = input(template.substitute({
                'favorite': 'to write vocabularies on Google spreadsheet'
                })) 
                
            if is_yes.lower() == 'y' or is_yes.lower() == 'yes':
                # Set up GSS
                self.is_GSS = True
                self.GSS = GoogleSpreadSheet(
                            self.config['GOOGLE_API']['JSONF_DIR'], 
                            self.config['GOOGLE_API']['JSON_FILE'], 
                            self.config['GOOGLE_API']['SPREAD_SHEET_KEY'], 
                            self.config['GOOGLE_API']['SPREAD_SHEET_NAME'],
                            self.config['TABLE']['COLUMNS'])
                
                # Retrieve Examples
                self.examples = OwnExampleSentence(self.examples_file_path)
                break
            elif is_yes.lower() == 'n' or is_yes.lower() == 'no':
                break
        
        # Ask you want to write vocabularies on CSV
        while True:
            template = console.get_template('ask_favorite.txt', self.speak_color)
            is_yes = input(template.substitute({
                'favorite': 'to write vocabularies on CSV'
                })) 

            if is_yes.lower() == 'y' or is_yes.lower() == 'yes':
                self.is_CSV = True
                self.CSV = CSV(self.config['TABLE']['COLUMNS'])
                break
            elif is_yes.lower() == 'n' or is_yes.lower() == 'no':
                break
        
        if self.is_GSS == False and self.is_CSV == False:
            quit()
        
        self.vocabulary = Vocabulary()
        self.scraping = FromCambridge()

        return None


    def get_urls(self):
        ''' '''
        self.url = FromBookmarks(self.bookmarks_file_path, self.config['BOOKMARKS']['FOLDER_NAME'])
        urls_num = len(self.url.urls)

        template = console.get_template('how_many_urls.txt', self.speak_color)
        print(template.substitute({'urls': urls_num}))

        return None


    def write_vocabularies(self):
        for url in self.url.urls:
            # Get vocabulary from URL
            self.vocabulary = self.scraping.scraping(url, self.vocabulary)
            self.result['scraping'].append(self.vocabulary.title)

            # Get examples
            for example in self.examples:
                if example['title'] == self.vocabulary.title:
                    self.vocabulary.example_sentence = example['example_sentence']
                    self.vocabulary.own_example = True
                    continue

            if self.is_GSS == True:
                if self.vocabulary.title in self.GSS.all_vocabularies:
                    self.result['voc_not_written'].append(self.vocabulary.title)
                    self.result['ex_not_written'].append(self.vocabulary.title)
                    continue
                self.GSS.write(self.vocabulary, self.result)
                
                if self.vocabulary.own_example == True:
                    self.result['ex_written'].append(self.vocabulary.title)
                else:
                    self.result['ex_not_written'].append(self.vocabulary.title)
                
            if self.is_CSV == True:
                self.CSV.write(self.vocabulary, self.config['PATH_CSV'] + self.config['FILE_CSV'])
        return None


    def show_result(self):
        template = console.get_template('result.txt', self.speak_color)
        print(template.substitute({ 'num_urls':     len(self.url.urls),
                                    'num_scraping': len(self.result['scraping']),

                                    'num_voc_written':     len(self.result['voc_written']),
                                    'num_voc_not_written': len(self.result['voc_not_written']),
                                    'num_ex_written':      len(self.result['ex_written']),
                                    'num_ex_not_written':  len(self.result['ex_not_written']),

                                    'voc_written':      self.result['voc_written'],
                                    'voc_not_written':  self.result['voc_not_written'],
                                    'ex_written':       self.result['ex_written'],
                                    'ex_not_written':   self.result['ex_not_written']}))
    

    def ask_to_delete(self):
        # Ask to delete Bookmarks
        template = console.get_template('ask_to_delete_file.txt', self.speak_color)
        is_yes = input(template.substitute({'path': self.config['PATH_BOOKMARKS'] + self.config['FILE_BOOKMARKS']}))
        if is_yes.lower() == 'y' or is_yes.lower() == 'yes':
            print(self.config['PATH_BOOKMARKS'] + self.config['FILE_BOOKMARKS'], 'has been deleted')
            helper.delete_file(self.config['PATH_BOOKMARKS'] + self.config['FILE_BOOKMARKS'])
        
        # Ask to delete Examples
        template = console.get_template('ask_to_delete_file.txt', self.speak_color)
        is_yes = input(template.substitute({'path': self.config['PATH_EX'] + self.config['FILE_EX']}))
        if is_yes.lower() == 'y' or is_yes.lower() == 'yes':
            print(self.config['PATH_EX'] + self.config['FILE_EX'], 'has been deleted')
            helper.delete_file(self.config['PATH_EX'] + self.config['FILE_EX'])

        # Ask to delete CSV
        template = console.get_template('ask_to_delete_file.txt', self.speak_color)
        is_yes = input(template.substitute({'path': self.config['PATH_CSV'] + self.config['FILE_CSV']}))
        if is_yes.lower() == 'y' or is_yes.lower() == 'yes':
            print(self.config['PATH_CSV'] + self.config['FILE_CSV'], 'has been deleted')
            helper.delete_file(self.config['PATH_CSV'] + self.config['FILE_CSV'])


    def ending(self):
        # Ending
        # Policy: we don't touch the origin Bookmarks file directly
        template = console.get_template('ending.txt', self.speak_color)
        print(template.substitute())