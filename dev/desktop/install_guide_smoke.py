"""Frozen EXE design-preview checks; no real device or build actions."""
def run(folder):
    from pathlib import Path
    from unittest.mock import patch
    from PySide6 import QtCore,QtWidgets as W
    from desktopapp import window
    root=Path(folder);root.mkdir(parents=True,exist_ok=False)
    app=W.QApplication.instance()or W.QApplication([])
    checks=[];metrics={}
    with patch.object(window,'load_settings',return_value={'firmware_update_version':'3.01'}):view=window.Window(demo=True)
    try:
        view.timer.stop();guide=view.install_guide
        view.resize(1100,820);view.show();app.processEvents()
        assert view.pages.currentIndex()==0 and guide.steps.currentIndex()==0
        visible=[view.nav.item(i).text()for i in range(view.nav.count())if not view.nav.item(i).isHidden()]
        assert visible[0]=='安装向导'and visible[-1]=='高级设置'and'连接设置'not in visible
        assert not guide.findChildren(W.QTabBar)and guide.progress.text()=='第 1 步 / 共 4 步'
        assert guide.steps.count()==4
        assert not any('准备 SD 卡'in label.text()for label in guide.findChildren(W.QLabel))
        assert view.text('firmware_update_version')=='3.11'and view.firmware_args()['update_version']=='3.11'
        checks.append('saved_301_does_not_override_default_311_and_no_SD_step')
        checks.append('default_wizard_and_advanced_settings_preserved')
        driver=guide.steps.widget(0);generator=guide.steps.widget(1)
        for action in ('driver_scan','usb_prepare','driver_install','connect','usb_stability','driver_uninstall'):
            assert driver.findChild(W.QPushButton,'action_'+action)
        assert driver.findChild(W.QPushButton,'zadig_guide')
        assert driver.isAncestorOf(view.driver_identity)
        checks.append('original_complete_driver_panel_in_wizard')
        assert generator.isAncestorOf(view.fields['firmware_source'])
        assert generator.isAncestorOf(view.fields['firmware_output'])
        for name in ('fl23','wb','sound','looks','vertical','ssh','voice'):
            assert generator.isAncestorOf(getattr(view,'local_'+name))
        assert generator.isAncestorOf(view.firmware_look_editor)
        assert not any(key.startswith('guide_')for key in view.fields)
        checks.append('original_complete_generator_no_duplicate_fields')
        with patch.object(view,'launch',side_effect=AssertionError('Navigation invoked an action')):
            for expected in (1,2,3,0):
                assert guide.next.isEnabled();guide.next.click();app.processEvents()
                assert guide.steps.currentIndex()==expected
            guide.go(3);assert guide.steps.currentIndex()==3
            guide.back.click();assert guide.steps.currentIndex()==2
        assert guide.built is None and guide.pending is None and not guide.configured
        checks.append('all_steps_navigable_without_files_camera_or_completed_actions')
        guide.go(2);app.processEvents()
        app.processEvents()
        metrics['short_step_height']=guide.steps.height()
        metrics['short_step_hint']=guide.steps.sizeHint().height()
        metrics['short_guide_height']=guide.height()
        assert guide.height()<400
        assert guide.steps.sizeHint().height()<300
        assert guide.steps.height()<350
        assert guide.steps.widget(3).layout().alignment()&QtCore.Qt.AlignTop
        metrics['window_height']=view.height()
        guide.go(0);app.processEvents()
        column=guide.panels[0][2];layout=column.layout()
        rectangles=[layout.itemAt(i).geometry()for i in range(layout.count())
                    if layout.itemAt(i).layout()or (layout.itemAt(i).widget()and not layout.itemAt(i).widget().isHidden())]
        gaps=[b.top()-a.bottom()-1 for a,b in zip(rectangles,rectangles[1:])]
        metrics['driver_max_widget_gap']=max(gaps)
        assert max(gaps)<40
        checks.append('short_steps_top_aligned_and_driver_spacing_compact')
        source=root/'官方 固件.DAT';source.write_bytes(b'UI fixture only')
        card=root/'SD 卡目录';card.mkdir()
        with patch.object(W.QFileDialog,'getExistingDirectory',return_value=str(card)):
            view.browse(view.fields['firmware_output'],'directory','All files (*)')
        assert view.firmware_args()['workspace']==str(card)
        checks.append('selected_SD_directory_is_generator_output_without_extra_step')
        view.fields['firmware_source'].setText(str(source))
        view.select_page('firmware');app.processEvents()
        assert view.page_widgets['firmware'].isAncestorOf(view.fields['firmware_source'])
        assert view.text('firmware_source')==str(source)
        view.select_page('drivers')
        assert view.page_widgets['drivers'].isAncestorOf(view.driver_identity)
        view.select_page('install');app.processEvents()
        assert driver.isAncestorOf(view.driver_identity)
        assert generator.isAncestorOf(view.fields['firmware_source'])
        assert view.text('firmware_source')==str(source)
        for _ in range(3):
            view.select_page('firmware');view.select_page('install')
        assert len(view.findChildren(W.QPushButton,'action_firmware_build'))==1
        checks.append('same_panels_return_to_sidebar_without_duplication_or_lost_fields')
        view.fields['firmware_source'].clear();guide.go(1)
        with patch.object(W.QMessageBox,'information')as popup,patch.object(window.jobs,'new_job',side_effect=AssertionError('Missing file reached worker')):
            guide.build_button.click()
            assert popup.call_count==1 and popup.call_args.args[1]=='请选择本地固件'
        assert guide.pending is None
        checks.append('actual_generate_still_prompts_for_missing_local_file')
        with patch.object(view,'launch',return_value=True)as launch:
            guide.driver_button.click();assert launch.call_count==1 and launch.call_args.args[0]=='usb_prepare'
        guide.finished({'action':'usb_prepare'},False)
        assert '未完成'in guide.driver_status.text()and guide.next.isEnabled()
        view.fields['firmware_source'].setText(str(source))
        guide.go(1)
        with patch.object(view,'launch',return_value=True)as launch:
            guide.build_button.click()
            assert launch.call_count==1 and launch.call_args.args[0]=='firmware_build'
            assert launch.call_args.args[1]['sony_firmware']==str(source)
        guide.finished({'action':'firmware_build'},False)
        assert guide.next.isEnabled()and not guide.configured
        checks.append('existing_action_routes_and_failure_not_treated_as_completion')
        view.select_page('advanced')
        assert view.page_widgets['advanced'].isAncestorOf(view.fields['ssh_update_ip'])
        assert view.page_widgets['advanced'].findChild(W.QPushButton,'action_ssh_connect')
        view.select_page('advanced');assert view.pages.currentWidget()is view.page_widgets['advanced']
        checks.append('connection_settings_inside_advanced_and_old_links_redirect')
        assert view.page_widgets['advanced'].findChild(W.QPushButton,'action_usb_set_version')
        assert view.page_widgets['recovery'].findChild(W.QPushButton,'action_usb_set_version')is None
        for name in ('trust_record','trust_source','trust_output','factory_failed_work'):assert name not in view.fields
        checks.append('previous_advanced_and_removed_controls_preserved')
        view.select_page('install');guide.go(1)
        assert view.firmware_sound_args()is None and view.firmware_sound_panel.isHidden()
        assert isinstance(view.local_custom_sound,W.QRadioButton)and view.local_default_sound.isChecked()
        assert view.local_sound_panel.property('subpanel')==view.local_looks_panel.property('subpanel')
        view.local_custom_sound.setChecked(True);assert not view.firmware_sound_panel.isHidden()
        view.fields['firmware_sound_source'].setText(str(source))
        view.firmware_sound_start.setValue(.15);view.firmware_sound_duration.setValue(.2)
        view.firmware_sound_mechanical.setChecked(True)
        for _ in range(3):app.processEvents()
        def inside(widget,parent):
            rect=QtCore.QRect(widget.mapTo(parent,QtCore.QPoint()),widget.size())
            assert parent.rect().contains(rect),(widget.objectName(),rect,parent.size())
        for size in ((1100,820),(950,720),(1400,900)):
            view.resize(*size)
            for _ in range(3):app.processEvents()
            for widget in (view.fields['firmware_sound_source'],view.firmware_sound_start,
                           view.firmware_sound_duration,view.firmware_sound_electronic,view.firmware_sound_mechanical):
                inside(widget,view.firmware_sound_panel)
                assert widget.height()>=widget.fontMetrics().height(),(type(widget).__name__,widget.height(),widget.fontMetrics().height())
            inside(view.firmware_sound_panel,view.local_sound_panel)
            for index in range(1,7):
                label=view.findChild(W.QLabel,'firmwareDefaultLookName%d'%index)
                inside(label,view.local_looks_panel)
                assert label.height()>=label.fontMetrics().height()
            form=view.firmware_sound_panel.layout();previous=None
            for row in range(form.rowCount()):
                boxes=[form.itemAt(row,role).geometry()for role in (W.QFormLayout.LabelRole,W.QFormLayout.FieldRole,W.QFormLayout.SpanningRole)
                       if form.itemAt(row,role)is not None]
                bounds=boxes[0]
                for box in boxes[1:]:bounds=bounds.united(box)
                if previous is not None:assert previous.bottom()<bounds.top(),(previous,bounds)
                previous=bounds
        metrics['expanded_generator_geometry_widths']=[950,1100,1400]
        checks.append('matching_sound_radio_panel_and_no_clipping_or_overlapping_rows')
        with patch.object(view,'launch',return_value=True)as launch:
            guide.build_button.click()
            spec=launch.call_args.args[1]['custom_sound']
            assert spec==dict(source=str(source),start=.15,duration=.2,selection='both')
        guide.finished({'action':'firmware_build'},False)
        view.local_sound.setChecked(False)
        assert view.firmware_sound_args()is None and view.firmware_sound_panel.isHidden()
        checks.append('custom_shutter_file_clip_targets_reach_existing_generator')
        return dict(passed=True,version='3.11',checks=checks,layout_metrics=metrics,
                    camera_io=False,actual_firmware_built=False,screenshots=False)
    finally:view.close()
