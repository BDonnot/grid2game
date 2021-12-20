import dash

def add_callbacks(dash_app, viz_server):
    dash_app.callback([dash.dependencies.Output("gofast-button", "children")],
                            [dash.dependencies.Input("nb_step_go_fast", "value")]
                            )(viz_server.change_nb_step_go_fast)

    # handle the press to one of the button to change the units
    dash_app.callback([dash.dependencies.Output("unit_trigger_rt_graph", "n_clicks"),
                            dash.dependencies.Output("unit_trigger_for_graph", "n_clicks"),
                            ],
                            [dash.dependencies.Input("line-info-dropdown", "value"),
                            dash.dependencies.Input("line-side-dropdown", "value"),
                            dash.dependencies.Input("load-info-dropdown", "value"),
                            dash.dependencies.Input("gen-info-dropdown", "value"),
                            dash.dependencies.Input("stor-info-dropdown", "value")
                            ],
                            [dash.dependencies.State("unit_trigger_rt_graph", "n_clicks"),
                            dash.dependencies.State("unit_trigger_for_graph", "n_clicks")]
                            )(viz_server.unit_clicked)

    # handle the interaction with the graph
    dash_app.callback([dash.dependencies.Output("do_display_action", "value"),

                            dash.dependencies.Output("generator_clicked", "style"),
                            dash.dependencies.Output("gen-redisp-curtail", "children"),
                            dash.dependencies.Output("gen-id-hidden", "children"),
                            dash.dependencies.Output("gen-id-clicked", "children"),
                            dash.dependencies.Output("gen-dispatch", "min"),
                            dash.dependencies.Output("gen-dispatch", "max"),
                            dash.dependencies.Output("gen-dispatch", "value"),
                            dash.dependencies.Output("gen_p", "children"),
                            dash.dependencies.Output("target_disp", "children"),
                            dash.dependencies.Output("actual_disp", "children"),

                            dash.dependencies.Output("storage_clicked", "style"),
                            dash.dependencies.Output("storage-id-hidden", "children"),
                            dash.dependencies.Output("stor-id-clicked", "children"),
                            dash.dependencies.Output("storage-power-input", "min"),
                            dash.dependencies.Output("storage-power-input", "max"),
                            dash.dependencies.Output("storage-power-input", "value"),
                            dash.dependencies.Output("storage_p", "children"),
                            dash.dependencies.Output("storage_energy", "children"),

                            dash.dependencies.Output("line_clicked", "style"),
                            dash.dependencies.Output("line-id-hidden", "children"),
                            dash.dependencies.Output("line-id-clicked", "children"),
                            dash.dependencies.Output("line-status-input", "value"),
                            dash.dependencies.Output("line_flow", "children"),

                            dash.dependencies.Output("sub_clicked", "style"),
                            dash.dependencies.Output("sub-id-hidden", "children"),
                            dash.dependencies.Output("sub-id-clicked", "children"),
                            dash.dependencies.Output("graph_clicked_sub", "figure"),
                            ],
                            [dash.dependencies.Input('real-time-graph', 'clickData'),
                            dash.dependencies.Input("back-button", "n_clicks"),
                            dash.dependencies.Input("step-button", "n_clicks"),
                            dash.dependencies.Input("simulate-button", "n_clicks"),
                            dash.dependencies.Input("go-button", "n_clicks"),
                            dash.dependencies.Input("gofast-button", "n_clicks"),
                            dash.dependencies.Input("go_till_game_over-button", "n_clicks"),
                            ]
                            )(viz_server.display_click_data)

    # handle display of the action, if needed
    dash_app.callback([dash.dependencies.Output("current_action", "children"),
                            ],
                            [dash.dependencies.Input("which_action_button", "value"),
                            dash.dependencies.Input("do_display_action", "value"),
                            dash.dependencies.Input("gen-redisp-curtail", "children"),
                            dash.dependencies.Input("gen-id-hidden", "children"),
                            dash.dependencies.Input('gen-dispatch', "value"),
                            dash.dependencies.Input("storage-id-hidden", "children"),
                            dash.dependencies.Input('storage-power-input', "value"),
                            dash.dependencies.Input("line-id-hidden", "children"),
                            dash.dependencies.Input('line-status-input', "value"),
                            dash.dependencies.Input('sub-id-hidden', "children"),
                            dash.dependencies.Input("graph_clicked_sub", "clickData")
                            ])(viz_server.display_action_fun)

    # handle the interaction with self.env, that should be done all in one function, otherwise
    # there are concurrency issues
    dash_app.callback([
        # trigger the computation if needed
        dash.dependencies.Output("trigger_computation", "value"),
        # update the button color / shape / etc. if needed
        dash.dependencies.Output("step-button", "className"),
        dash.dependencies.Output("simulate-button", "className"),
        dash.dependencies.Output("back-button", "className"),
        dash.dependencies.Output("reset-button", "className"),
        dash.dependencies.Output("go-button", "className"),
        dash.dependencies.Output("gofast-button", "className"),
                        ],
                        [dash.dependencies.Input("step-button", "n_clicks"),
                        dash.dependencies.Input("simulate-button", "n_clicks"),
                        dash.dependencies.Input("back-button", "n_clicks"),
                        dash.dependencies.Input("reset-button", "n_clicks"),
                        dash.dependencies.Input("go-button", "n_clicks"),
                        dash.dependencies.Input("gofast-button", "n_clicks"),
                        dash.dependencies.Input("go_till_game_over-button", "n_clicks"),
                        dash.dependencies.Input("untilgo_butt_call_act_on_env", "value"),
                        dash.dependencies.Input("selfloop_call_act_on_env", "value"),
                        dash.dependencies.Input("timer", "n_intervals")
                        ],
                        [dash.dependencies.State("act_on_env_trigger_rt", "n_clicks"),
                        dash.dependencies.State("act_on_env_trigger_for", "n_clicks"),
                        dash.dependencies.State("act_on_env_call_selfloop", "value")]
                        )(viz_server.handle_act_on_env)

    dash_app.callback([dash.dependencies.Output("act_on_env_trigger_rt", "n_clicks"),
                            dash.dependencies.Output("act_on_env_trigger_for", "n_clicks")],
                            [dash.dependencies.Input("trigger_computation", "value"),
                            dash.dependencies.Input("recompute_rt_from_timeline", "n_clicks")]
                            )(viz_server.computation_wrapper)

    # handle triggers: refresh of the figures for real time (graph part)
    dash_app.callback([dash.dependencies.Output("figrt_trigger_temporal_figs", "n_clicks"),
                            dash.dependencies.Output("figrt_trigger_rt_graph", "n_clicks"),
                            dash.dependencies.Output("figrt_trigger_for_graph", "n_clicks"),
                            dash.dependencies.Output("scenario_progression", "value"),
                            dash.dependencies.Output("scenario_progression", "children"),
                            dash.dependencies.Output("scenario_progression", "color"),
                            dash.dependencies.Output("timeline_graph", "figure"),
                            ],
                            [dash.dependencies.Input("act_on_env_trigger_rt", "n_clicks")],
                            []
                            )(viz_server.update_rt_fig)

    # handle triggers: refresh of the figures for the forecast
    dash_app.callback([dash.dependencies.Output("figfor_trigger_for_graph", "n_clicks")],
                            [dash.dependencies.Input("act_on_env_trigger_for", "n_clicks"),
                            ],
                            []
                            )(viz_server.update_simulated_fig)

    # final graph display
    # handle triggers: refresh the figures (temporal series part)
    dash_app.callback([
                        dash.dependencies.Output("graph_gen_load", "figure"),
                        dash.dependencies.Output("graph_flow_cap", "figure"),
                        ],
                        [dash.dependencies.Input("figrt_trigger_temporal_figs", "n_clicks"),
                        dash.dependencies.Input("showtempo_trigger_rt_graph", "n_clicks")
                        ],
                        )(viz_server.update_temporal_figs)

    # dash_app.callback([dash.dependencies.Output('temporal_graphs', "style"),
    #                    dash.dependencies.Output("showtempo_trigger_rt_graph", "n_clicks")
    #                    ],
    #                   [dash.dependencies.Input('show-temporal-graph', "value")]
    #                   )(self.show_hide_tempo_graph)

    # handle final graph of the real time grid
    dash_app.callback([dash.dependencies.Output("real-time-graph", "figure"),
                            dash.dependencies.Output("rt_date_time", "children")],
                            [dash.dependencies.Input("figrt_trigger_rt_graph", "n_clicks"),
                            dash.dependencies.Input("unit_trigger_rt_graph", "n_clicks"),
                            ]
                            )(viz_server.update_rt_graph_figs)

    # handle final graph for the forecast grid
    dash_app.callback([dash.dependencies.Output("simulated-graph", "figure"),
                            dash.dependencies.Output("forecast_date_time", "children")],
                            [dash.dependencies.Input("figrt_trigger_for_graph", "n_clicks"),
                            dash.dependencies.Input("figfor_trigger_for_graph", "n_clicks"),
                            dash.dependencies.Input("unit_trigger_for_graph", "n_clicks"),
                            ]
                            )(viz_server.update_for_graph_figs)

    # load the assistant
    dash_app.callback([dash.dependencies.Output("current_assistant_path", "children"),
                            dash.dependencies.Output("clear_assistant_path", "n_clicks")],
                            [dash.dependencies.Input("load_assistant_button", "n_clicks")],
                            [dash.dependencies.State("select_assistant", "value")]
                            )(viz_server.load_assistant)

    dash_app.callback([dash.dependencies.Output("select_assistant", "value")],
                            [dash.dependencies.Input("clear_assistant_path", "n_clicks")]
                            )(viz_server.clear_loading)

    dash_app.callback([dash.dependencies.Output("current_save_path", "children")],
                            [dash.dependencies.Input("save_expe_button", "n_clicks")],
                            [dash.dependencies.State("save_expe", "value")]
                            )(viz_server.save_expe)

    # callback for the timeline
    dash_app.callback([dash.dependencies.Output("recompute_rt_from_timeline", "n_clicks")],
                            [dash.dependencies.Input('timeline_graph', 'clickData')])(viz_server.timeline_set_time)