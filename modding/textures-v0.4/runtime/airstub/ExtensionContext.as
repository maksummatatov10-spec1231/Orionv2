package flash.external {
  import flash.events.EventDispatcher;
  public class ExtensionContext extends EventDispatcher {
    public static function createExtensionContext(domain:String, contextType:String):ExtensionContext {
      return new ExtensionContext();
    }
    public function call(functionName:String, ...args):Object {
      if (functionName == "AIRSteam_Init") return false;
      if (functionName == "AIRSteam_GetUserID" || functionName == "AIRSteam_GetAppID") return "0";
      if (functionName == "AIRSteam_GetCurrentGameLanguage") return "english";
      if (functionName == "AIRSteam_GetAvailableGameLanguages") return "english";
      if (functionName == "AIRSteam_GetPersonaName") return "Player";
      return null;
    }
    public function dispose():void {}
  }
}
