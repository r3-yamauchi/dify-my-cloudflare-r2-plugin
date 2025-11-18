"""
場所: main.py
内容: Dify プラグインの起動ポイント。
目的: プロセス開始時にプラグインを実行する。
"""

from dify_plugin import Plugin, DifyPluginEnv

plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=120))

if __name__ == '__main__':
    plugin.run()




