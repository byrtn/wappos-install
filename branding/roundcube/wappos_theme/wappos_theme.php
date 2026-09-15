<?php
// Auteur : Patrick Ritaine

class wappos_theme extends rcube_plugin
{
    function init()
    {
        $this->include_stylesheet('wappos-theme.css');
        $this->add_hook('template_object_skininfo', [$this, 'skininfo']);
    }

    public static function info()
    {
        return [
            'name' => 'wappos_theme',
            'version' => '1.0',
            'license' => 'GPL-3.0+',
        ];
    }

    public function skininfo($args)
    {
        $args['content'] = html::p(null,
            html::span('skinitem',
                html::span('skinauthor', 'Le thème Wappos est une adaptation par Patrick Ritaine du thème Elastic par Aleksander Machniak')
            )
        );

        return $args;
    }
}
