# Slack Jenkins Remote

Integrates with Slack slash commands API and Jenkins, providing you access to do control Jenkins builds from Slack.

Commands supported (assuming you use `/build` as the command):

 - `/build` - Shows help
 - `/build help` - Shows help
 - `/build JOB` - Runs `JOB` with default parameters
 - `/build JOB --param=value` - Runs `job` with `param=value` (or `PARAM=value` depending on settings)
 
Notifies channel it was run on about progress.

Licensed under the new BSD and MIT licenses (`LICENSE.md`).


## Setup

Set up a server with access to your Jenkins instance, that can terminate SSL and proxy requests to SJR, Nginx is well suitable for that job.

Run SJR somehow, behind that SSL terminating reverse proxy. Notice that the SSL certificate needs to validate properly. https://api.slack.com/slash-commands#ssl

Add a Slash command for your Slack: https://my.slack.com/services/new/slash-commands

Copy `settings.template.py` to `settings.py` and edit to taste, and to match e.g. the token given to you by Slack.


## Testing

For testing you can run SJR fairly easily, just make sure you have `virtualenv` available in your `PATH` and run: 

```bash
bash run.sh
```

*NOTICE:* For some odd reason it seems that after starting Flask like this you have to hit `CTRL+C` once to get it to process everything properly.


# Financial support

This project has been made possible thanks to [Cocreators](https://cocreators.ee) and [Lietu](https://lietu.net). You can help us continue our open source work by supporting us on [Buy me a coffee](https://www.buymeacoffee.com/cocreators).

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cocreators)
