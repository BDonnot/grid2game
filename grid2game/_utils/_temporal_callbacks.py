# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Game, Grid2Game a gamified platform to interact with grid2op environments.

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
                       dash.dependencies.State("unit_trigger_for_graph", "n_clicks")
                      ]
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
                    #    dash.dependencies.Output("graph_clicked_sub", "figure"),
                       dash.dependencies.Output("update_substation_layout_clicked_from_grid", "n_clicks"),
                      ],
                      [dash.dependencies.Input('real-time-graph', 'clickData'),
                       dash.dependencies.Input("back-button", "n_clicks"),
                       dash.dependencies.Input("step-button", "n_clicks"),
                       dash.dependencies.Input("simulate-button", "n_clicks"),
                       dash.dependencies.Input("go-button", "n_clicks"),
                       dash.dependencies.Input("gofast-button", "n_clicks"),
                       dash.dependencies.Input("go_till_game_over-button", "n_clicks"),
                      ])(viz_server.display_click_data)

    # handle display of the action, if needed
    dash_app.callback([dash.dependencies.Output("current_action", "children"),
                       dash.dependencies.Output("which_action_button", "value"),
                       dash.dependencies.Output("update_substation_layout_clicked_from_sub", "n_clicks")
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

    # plot the substation that changes when we click
    dash_app.callback([dash.dependencies.Output("graph_clicked_sub", "figure")],
                      [dash.dependencies.Input("update_substation_layout_clicked_from_sub", "n_clicks"),
                       dash.dependencies.Input("update_substation_layout_clicked_from_grid", "n_clicks"),
                      ])(viz_server.display_grid_substation)

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
                       dash.dependencies.Output("go_till_game_over-button", "className"),
                       dash.dependencies.Output("is_computing_left", "style"),
                       dash.dependencies.Output("is_computing_right", "style"),
                       dash.dependencies.Output("change_graph_title", "n_clicks"),
                       dash.dependencies.Output("update_progress_bar_from_act", "n_clicks")
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
                       dash.dependencies.State("act_on_env_call_selfloop", "value")
                      ]
                     )(viz_server.handle_act_on_env)

    dash_app.callback([dash.dependencies.Output("act_on_env_trigger_rt", "n_clicks"),
                       dash.dependencies.Output("act_on_env_trigger_for", "n_clicks")
                      ],
                      [dash.dependencies.Input("trigger_computation", "value"),
                       dash.dependencies.Input("recompute_rt_from_timeline", "n_clicks")
                      ]
                      )(viz_server.computation_wrapper)

    # handle triggers: refresh of the figures for real time (graph part)
    dash_app.callback([dash.dependencies.Output("figrt_trigger_temporal_figs", "n_clicks"),
                       dash.dependencies.Output("figrt_trigger_rt_graph", "n_clicks"),
                       dash.dependencies.Output("figrt_trigger_for_graph", "n_clicks"),
                       dash.dependencies.Output("timeline_graph", "figure"),
                       dash.dependencies.Output("update_progress_bar_from_figs", "n_clicks")
                      ],
                      [dash.dependencies.Input("act_on_env_trigger_rt", "n_clicks")],
                      []
                     )(viz_server.update_rt_fig)

    dash_app.callback([
                       dash.dependencies.Output("scenario_progression", "value"),
                       dash.dependencies.Output("scenario_progression", "label"),
                       dash.dependencies.Output("scenario_progression", "color"),
                      ],[
                       dash.dependencies.Input("update_progress_bar_from_act", "n_clicks"),
                       dash.dependencies.Input("update_progress_bar_from_figs", "n_clicks"),
                      ])(viz_server.update_progress_bar)
    # handle triggers: refresh of the figures for the forecast
    dash_app.callback([dash.dependencies.Output("figfor_trigger_for_graph", "n_clicks")],
                      [dash.dependencies.Input("act_on_env_trigger_for", "n_clicks")],
                      []
                     )(viz_server.update_simulated_fig)

    # final graph display
    # handle triggers: refresh the figures (temporal series part)
    dash_app.callback([dash.dependencies.Output("graph_gen_load", "figure"),
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
                       dash.dependencies.Output("rt_date_time", "children"),
                       dash.dependencies.Output("trigger_rt_extra_info", "n_clicks")
                      ],
                      [dash.dependencies.Input("figrt_trigger_rt_graph", "n_clicks"),
                       dash.dependencies.Input("unit_trigger_rt_graph", "n_clicks"),
                      ]
                     )(viz_server.update_rt_graph_figs)

    # handle final graph for the forecast grid
    dash_app.callback([dash.dependencies.Output("simulated-graph", "figure"),
                       dash.dependencies.Output("forecast_date_time", "children"),
                       dash.dependencies.Output("trigger_for_extra_info", "n_clicks")
                      ],
                      [dash.dependencies.Input("figrt_trigger_for_graph", "n_clicks"),
                       dash.dependencies.Input("figfor_trigger_for_graph", "n_clicks"),
                       dash.dependencies.Input("unit_trigger_for_graph", "n_clicks"),
                      ]
                     )(viz_server.update_for_graph_figs)

    if viz_server._app_heroku is False:
        # this is deactivated on heroku at the moment !
        # load the assistant
        dash_app.callback([dash.dependencies.Output("current_assistant_path", "children"),
                           dash.dependencies.Output("clear_assistant_path", "n_clicks"),
                           dash.dependencies.Output("loading_assistant_output", "children"),
                          ],
                          [dash.dependencies.Input("load_assistant_button", "n_clicks")
                          ],
                          [dash.dependencies.State("select_assistant", "value")]
                         )(viz_server.load_assistant)

        dash_app.callback([dash.dependencies.Output("select_assistant", "value")],
                          [dash.dependencies.Input("clear_assistant_path", "n_clicks")]
                         )(viz_server.clear_loading)

        # save the current experiment
        dash_app.callback([dash.dependencies.Output("current_save_path", "children"),
                           dash.dependencies.Output("loading_save_output", "children"),
                          ],
                          [dash.dependencies.Input("save_expe_button", "n_clicks")],
                          [dash.dependencies.State("save_expe", "value")]
                         )(viz_server.save_expe)

    # tell if action was illegal
    dash_app.callback([dash.dependencies.Output("forecast_extra_info", "style")],
                      [dash.dependencies.Input("trigger_for_extra_info", "n_clicks")]
                     )(viz_server.tell_illegal_for)
    dash_app.callback([dash.dependencies.Output("rt_extra_info", "style")],
                      [dash.dependencies.Input("trigger_rt_extra_info", "n_clicks")]
                     )(viz_server.tell_illegal_rt)

    # callback for the timeline
    dash_app.callback([dash.dependencies.Output("recompute_rt_from_timeline", "n_clicks")],
                      [dash.dependencies.Input('timeline_graph', 'clickData')])(viz_server.timeline_set_time)

    # callbacks when the "reset" button is pressed
    dash_app.callback([dash.dependencies.Output("scenario_id_title", "children"),
                       dash.dependencies.Output("scenario_seed_title", "children"),
                       dash.dependencies.Output("chronic_names", "value"),
                       dash.dependencies.Output("set_seed", "value"),
                      ],
                      [dash.dependencies.Input("change_graph_title", "n_clicks")])(viz_server.change_graph_title)

    # set the chronics
    dash_app.callback([dash.dependencies.Output("chronic_names_dummy_output", "n_clicks")],
                      [dash.dependencies.Input("chronic_names", "value")])(viz_server.set_chronics)

    # set the seed
    dash_app.callback([dash.dependencies.Output("set_seed_dummy_output", "n_clicks")],
                      [dash.dependencies.Input("set_seed", "value")])(viz_server.set_seed)
