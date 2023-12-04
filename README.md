# ScrapedIn
tool to scrape LinkedIn

this tool assists in performing reconnaissance using the LinkedIn.com website/API. Provide a search string just as you would on the original website and let ScrapedIn do all the dirty work. Output is stored as an XLSX file, however it is intended to be used with Google Spreadsheets. After importing the XLSX into Google Spreadsheets there will be a "dataset" worksheet and a "report" worksheet.

# Sponsorship
[<img src="proxycurl.png" width=350>](https://nubela.co/proxycurl?utm_campaign=influencer_marketing&utm_source=github&utm_medium=social&utm_content=daniel_chrastil_scrapedin)

> Scrape public LinkedIn profile data at scale with [Proxycurl APIs](https://nubela.co/proxycurl?utm_campaign=influencer_marketing&utm_source=github&utm_medium=social&utm_content=daniel_chrastil_scrapedin).
> - Scraping Public profiles are battle-tested in court in HiQ VS LinkedIn case.
> - GDPR, CCPA, SOC2 compliant
> - High rate Limit - 300 requests/minute
> - Fast APIs respond in ~2s
> - Fresh data - 88% of data is scraped real-time, other 12% are not older than 29 days
> - High accuracy
> - Tons of data points returned per profile
>
> Built for developers, by developers.

## dataset
- first name
- last name
- occupation
- location
- industry
- profile URL
- picture URL

## report
- Picture (displayed)
- Full Name, Occupation
- Link to Profile

### Disclaimer
this tool is for educational purposes only and violates LinkedIn.com's TOS. Use at your own risk.

## Screenshots

![alt tag](https://s18.postimg.org/nh7dtdkux/Screen_Shot_2018-03-29_at_7.09.04_AM.png)

![alt tag](https://s4.postimg.org/vu9izninx/Screen_Shot_2017_03_15_at_11_45_11_PM.png)

![alt tag](https://s8.postimg.org/st0h8maxx/Screen_Shot_2017_03_20_at_11_04_00_AM.png)

## How to install
`sudo apt-get install python-pip -y`

`sudo pip install -r requirements.txt`
