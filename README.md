# ZHAW CAI News

A simple Flask-Webserver which displays the latest [news](https://www.zhaw.ch/en/engineering/institutes-centres/cai/#c165128) from the [Centre for Artificial Intelligence](https://www.zhaw.ch/en/engineering/institutes-centres/cai/) of the [Zurich University of Applied Sciences](https://www.zhaw.ch/en/university/).


![Sample News Page](https://user-images.githubusercontent.com/46379095/189369014-6caaf657-bd90-4dda-8ec8-ad20cd0fba28.png)


## Run the App

Please create first a .env file:

```bash
cp .env.example .env
```

Then install the dependencies:

```bash
uv sync
```

Finally, run the application:

```bash
uv run app.py
```

