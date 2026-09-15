<?php

declare(strict_types=1);

namespace OCA\WapposPolish\AppInfo;

use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Util;

class WapposPolishListener implements IEventListener {
	public function handle(Event $event): void {
		if (!($event instanceof BeforeTemplateRenderedEvent)) {
			return;
		}

		Util::addStyle(Application::APP_ID, 'style');
	}
}
