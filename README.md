# ActivityLogger

An application to track and report user activity.

## Track Activity

Run `TrackActivity.exe` to track your Windows activity. It will append your Windows activity to a weekly log file. The log file is a tab-delimited text file.

### Track CLI Options

You can use command line options to specify the following items:

| CLI_Option | Description | Default Behavior |
|:--:|:--|:--|
| `--folder` | Specify the location of the weekly log files. | Folder is current working directory. |
| `--inactive` | Specify the length of inactive time before the `TrackActivity.exe` application assumes that the user is inactive. The duration is just used to label the time as inactive. The actual start of the inactive time does not change. | Inactive threshold is 420 seconds (7 minutes). |
| `--sample` | Specify how often the `TrackActivity.exe` application should check the user activity for a change in state. Example a change in the Window title or a change to an inactive state. | Sampling period is 2 seconds. |

## Report Activity

Run `ReportActivity.exe` to report your weekly Windows activity. It will analyze a weekly log file.

### Report CLI Options

You can use command line options to specify the following items:

| CLI_Option | Description | Default Behavior |
|:--:|:--|:--|
| `--config` | Specify the path and filename for the JSON configuration file. | Path and filename is `./analysis.json`. |
| `--folder` | Specify the location of the weekly log files. | Folder is current working directory. |
| `--tagged` | Show all log file entries that matched any of the filters defined in the configuration file. The entries are sorted from the largest to smallest time to help you create filters for the most important items. | Do not show tagged log file entries. |
| `--untagged` | Show all log file entries that did not match any of the filters defined in the configuration file. The entries are sorted from the largest to smallest time to help you create filters for the most important items. | Do not show untagged log file entries. |
