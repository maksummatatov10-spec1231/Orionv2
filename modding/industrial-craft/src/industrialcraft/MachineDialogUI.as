package industrialcraft {
 import assets.Images;
 import flash.display.DisplayObjectContainer;
 import flash.events.MouseEvent;
 import orion.events.DialogEvent;
 import orion.ui.UIStyle;
 import orion.ui.base.ButtonUI;
 import orion.ui.base.DialogUI;
 import orion.ui.base.LabelUI;
 import orion.ui.base.PanelUI;
 import orion.ui.game.IInventoryUI;
 import orion.ui.game.ItemViewerUI;
 import orion.ui.game.player_dialog.InventoryPanelUI;
 import orion.worlds.ItemStack;
 import utils.Fonts;
 public final class MachineDialogUI extends DialogUI {
  private var state:MachineState;
  private var panel:MachinePanelUI;
  private var closeBtn:ButtonUI;
  private var moving:ItemViewerUI;
  private var movingStack:Boolean=false;
  private var marginX:Number=0;private var marginY:Number=0;
  public function MachineDialogUI(parent:DisplayObjectContainer,state:MachineState){this.state=state;super(parent);}
  override protected function addChildren():void {
   super.addChildren();
   var bg:PanelUI=new PanelUI(this).setImage(Images.GAME_INVENTORY_BACKGROUND);
   new LabelUI(bg,60,7).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setText(Text.getValue("ui_lbl_inventory")).setFont(Fonts.ZANTROKE,15,16767635).addFilter(UIStyle.BLACK_STROKE_FILTER).setSize(200,18);
   new LabelUI(bg,340,7).setAutoSize(false).setAlign(LabelUI.CENTER_ALIGN).setText("Калибровочный станок").setSystemFont("Verdana",13,16767635).setFontBold(true).addFilter(UIStyle.BLACK_STROKE_FILTER).setSize(280,18);
   new InventoryPanelUI(bg);
   panel=new MachinePanelUI(bg,state);bg.setChildIndex(panel,0);
   closeBtn=new ButtonUI(bg,610,4).setImage(Images.BUTTON_GAME_INVENTORY_EXIT).setSize(29,28) as ButtonUI;
   moving=new ItemViewerUI(this);moving.setIndex(-1);moving.mouseEnabled=false;moving.visible=false;
  }
  override protected function addEventListeners():void {
   super.addEventListeners();closeBtn.addEventListener(MouseEvent.CLICK,onClose);
   addEventListener(MouseEvent.CLICK,onClick);addEventListener(MouseEvent.MOUSE_MOVE,onMove);
  }
  override protected function removeEventListeners():void {
   super.removeEventListeners();closeBtn.removeEventListener(MouseEvent.CLICK,onClose);
   removeEventListener(MouseEvent.CLICK,onClick);removeEventListener(MouseEvent.MOUSE_MOVE,onMove);
  }
  private function onClose(e:MouseEvent):void{close();}
  override protected function close(cancel:Boolean=true):void {
   if(movingStack && moving.itemStack!=null)Context.world.dropPlayerItem(moving.itemStack);
   super.close(cancel);
  }
  private function onClick(e:MouseEvent):void {
   var viewer:ItemViewerUI=e.target as ItemViewerUI;if(viewer==null || viewer.index==-1)return;
   var inv:IInventoryUI=viewer.iInventoryUi;var current:ItemStack=viewer.itemStack;var held:ItemStack=moving.itemStack;
   if(held!=null && !inv.canSetItem(viewer,held))return;
   if(held!=null && current!=null && held.item==current.item && current.count<current.item.maxStackSize){
    var add:int=Math.min(held.count,current.item.maxStackSize-current.count);current.count+=add;held.count-=add;
    if(held.count<=0){moving.setItemStack(null);moving.visible=false;movingStack=false;}else moving.updateNow();
    viewer.updateNow();if(panel!=null)panel.refresh();return;
   }
   inv.setItem(viewer,held);moving.setItemStack(current);viewer.updateNow();
   movingStack=moving.itemStack!=null;moving.visible=movingStack;
   if(movingStack){marginX=e.localX;marginY=e.localY;moving.x=e.stageX-marginX;moving.y=e.stageY-marginY;moving.updateNow();}
   if(panel!=null)panel.refresh();
  }
  private function onMove(e:MouseEvent):void{if(movingStack){moving.x=e.stageX-marginX;moving.y=e.stageY-marginY;}}
 }
}
