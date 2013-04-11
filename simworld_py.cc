#include <Python.h>
// Simutrans include
#include <simworld.h>
#include <dataobj/koord.h>
#include <dataobj/koord3d.h>
#include <dataobj/einstellungen.h>

#include <simdebug.h> // For init logging
#include <simmenu.h>    // For werkzeug_t (init)
#include <dataobj/umgebung.h> // For setting debug level, and init fps

#include <bauer/fabrikbauer.h>  // For fabrik_besch_t table

#include <besch/reader/obj_reader.h> // for PAK loading

#include <dataobj/pakset_info.h> // For PAK WTF operaions

#include <besch/reader/groundobj_reader.h> // Try to fix the reader problems

#include <tpl/weighted_vector_tpl.h>    // Export the list of cities
#include <tpl/vector_tpl.h>         // Export consumers and suppliers list in Fab

#include <simcity.h>    // Export cities information
#include <dings/gebaeude.h> // Attempt to fix simcitiy compilation error

#include <simfab.h> // Export fabrik_t information
#include <utils/cbuffer_t.h>    // For fabrik info

// To init the quickstone lists
#include <halthandle_t.h>
#include <convoihandle_t.h>
#include <linehandle_t.h>

// Boost Python include
#include <boost/python.hpp>
using namespace boost::python;

// Trick to distingush between overloaded karte_t::load
bool (karte_t::*load_fname)(const char*) = &karte_t::load;

// Select overloaded karte_t::get_settings
//settings_t const& (karte_t::*karte_get_settings)() const = &karte_t::get_settings;
settings_t& (karte_t::*karte_get_settings)() = &karte_t::get_settings;

// Select overloaded koord_distance
uint32 (*koord_distance_koord_koord)(const koord&, const koord&) = &koord_distance;

const char* PAK_PATH = "pak128/";

// ********** WRAPPER for weighted_vector_tpl<T*>

template<class T>
const T* getitem_weighted_vector(weighted_vector_tpl<T*> &v, unsigned int index){
    if (index >= 0 && index < v.get_count()) {
        return (v[index]);
    } else {
        PyErr_SetString(PyExc_IndexError, "index out of range");
        throw_error_already_set();
        return NULL; // Remove warning
    }
}

template<class T>
void export_weighted_vector(std::string kname) {
    class_< weighted_vector_tpl<T*> , boost::noncopyable >( kname.c_str(), no_init )
        // Expose attributes in a c++ way
        .add_property("count", &weighted_vector_tpl<T*>::get_count )
        .add_property("capacity", &weighted_vector_tpl<T*>::get_size )
        // Expose attributes in a pythonic way
        .def("__len__", &weighted_vector_tpl<T*>::get_count )
        .def("__getitem__", &getitem_weighted_vector<T>,
            //return_value_policy<copy_const_reference>()
            return_value_policy<reference_existing_object>()
        )
    ;
}

// ********** WRAPPER for vector_tpl<T>

template<class T>
const T& getitem_vector_tpl(vector_tpl<T> &v, uint index) {
    static T nix; //TODO How it works
    if (index >= 0 && index < v.get_count()) {
        return v[index];
    } else {
        PyErr_SetString(PyExc_IndexError, "index out of range");
        throw_error_already_set();
    }
    return nix; // Remove warning
}

template<class T>
void export_vector_tpl(std::string kname) {
    class_< vector_tpl<T> , boost::noncopyable >( kname.c_str(), no_init )
        // Expose attributes in a c++ way
        .add_property("count", &vector_tpl<T>::get_count )
        .add_property("capacity", &vector_tpl<T>::get_size )
        // Expose attributes in a pythonic way
        .def("__len__", &vector_tpl<T>::get_count )
        .def("__getitem__", &getitem_vector_tpl<T>,
            return_value_policy<reference_existing_object>() )
            //return_value_policy<copy_const_reference>())
    ;
}

// ********** WRAPPER for array_tpl<T>

template<class T>
const T& getitem_array_tpl(array_tpl<T> &v, uint index) {
    static T nix; //TODO How it works
    if (index >= 0 && index < v.get_count()) {
        return v[index];
    } else {
        PyErr_SetString(PyExc_IndexError, "index out of range");
        throw_error_already_set();
    }
    return nix; // Remove warning
}

template<class T>
void export_array_tpl(std::string kname) {
    class_< array_tpl<T> , boost::noncopyable >( kname.c_str(), no_init )
        // Expose attributes in a c++ way
        .add_property("count", &array_tpl<T>::get_count )
        //.add_property("capacity", &array_tpl<T>::get_size )
        // Expose attributes in a pythonic way
        .def("__len__", &array_tpl<T>::get_count )
        .def("__getitem__", &getitem_array_tpl<T>,
            return_value_policy<copy_const_reference>()
        )
    ;
}

// ********** WRAPPER for stringhashtable_tpl< value_t >
template <class V>
list get_stringhashtable_tpl_keys(stringhashtable_tpl<V> const& self){
    list t;
    // TODO: Why my manual code is not working??
    //typedef typename stringhashtable_tpl<V>::const_iterator iter;
    //iter i = self.begin(), end = self.end();
    //for( ; i != end; ++i )
    //    t.append( i.key );
    FOR(stringhashtable_tpl<fabrik_besch_t const*>, const& i, self) {
        t.append( i.key );
    }
    return t;
}

template <class V>
list get_stringhashtable_tpl_values(stringhashtable_tpl<V> const& self){
    list t;
    FOR(stringhashtable_tpl<fabrik_besch_t const*>, const& i, self) {
        t.append( i.value );
    }
    return t;
}

template <class V>
list get_stringhashtable_tpl_itemss(stringhashtable_tpl<V> const& self){
    list t;
    FOR(stringhashtable_tpl<fabrik_besch_t const*>, const& i, self) {
        t.append( make_tuple( i.key, i.value) );
    }
    return t;
}

template <class V> //class stringhashtable_tpl :
void export_stringhashtable_tpl(std::string kname) {
    class_< stringhashtable_tpl<V>, boost::noncopyable >( kname.c_str(), no_init )
        .def("__len__", &stringhashtable_tpl<V>::get_count )
        .def("__getitem__", &stringhashtable_tpl<V>::get,
            return_value_policy<reference_existing_object>())
        .def("keys", &get_stringhashtable_tpl_keys<V> )
        .def("values", &get_stringhashtable_tpl_values<V> )
        .def("items", &get_stringhashtable_tpl_itemss<V> )
    ;
}

// Function to save a World with a given name
void save_welt(karte_t* welt, const char *filename){
    welt->save( filename, loadsave_t::save_mode, umgebung_t::savegame_version_str, false );
}

// Temporary function used to expose the factory count
// instead of exposing the property FIXME
uint32 karte_factory_count(karte_t* welt){
    return welt->get_fab_list().get_count();
}

// Handy get size as tuple
tuple settings_size_as_tuple(const settings_t &s){
    return make_tuple(s.get_groesse_x(), s.get_groesse_y());
}

// Handy __str__ for koord
std::ostream &operator<<(std::ostream &ostr, const koord &k) {
    ostr << "koord(" << k.x << ", " << k.y << ")";
    return ostr;
}

// Handy __str__ for koord3d
std::ostream &operator<<(std::ostream &ostr, const koord3d &k) {
    ostr << "koord3d(" << k.x << ", " << k.y << ", " << (short)(k.z) << ")";
    return ostr;
}

// Equality operator for besch
bool operator==(const ware_besch_t& self, const ware_besch_t& other){
    return self.get_index() == other.get_index();
}

// Handy tuple returning method for a koord
tuple koord_as_tuple(const koord &k) {
    return make_tuple(k.x, k.y);
}

void (*set_lang_int)(int) = &translator::set_language;
void (*set_lang_chr)(const char*) = &translator::set_language;
const char* (*translate_current_lang)(const char*) = &translator::translate;

const stringhashtable_tpl<const fabrik_besch_t*>& (*get_fabesch_table)() = &fabrikbauer_t::get_fabesch;

void print_work_dir(){
    dbg->important("Inited work dir %s", umgebung_t::program_dir);
}

BOOST_PYTHON_MODULE(simworld){

    //----------------------------------------
    // Initialization done in simmain

    umgebung_t::init();

    // Integral component
    //init_logging("test_simworld.log", true, true, "Simworld py TEST\n", NULL);
    dbg = new log_t("test_simworld.log", true, true, false,
            "Simworld python extension LOG\n", NULL);

    // Obey defaults at init
    //umgebung_t::verbose_debug = 2;

    // Test log levels
    dbg->error("PY", "Testing level error");
    dbg->warning("PY", "Testing level warning");
    dbg->important("Testing level important");
    dbg->message("PY", "Testing level message");
    dbg->debug("PY", "Testing level debug");

    // Test Debug messages
    DBG_MESSAGE("INIT_MODULE()","Doing a DBG MESSAGE %d");

#ifdef _WIN32
#define PATHSEP "\\"
#else
#define PATHSEP "/"
#endif
    const char* path_sep = PATHSEP;

    // Init program_dir to PWD
    getcwd(umgebung_t::program_dir, lengthof(umgebung_t::program_dir));
    strcat( umgebung_t::program_dir, path_sep );

    umgebung_t::user_dir = umgebung_t::program_dir;

    dbg->important("Inited work dir %s", umgebung_t::program_dir);

    //assert( obj_reader_t::obj_reader != NULL ); // obj_reader is private
    //obj_reader_t::init();
    groundobj_reader_t::instance(); // Fix to get the instances registered

    convoihandle_t::init( 1024 );
    linehandle_t::init( 1024 );
    halthandle_t::init( 1024 );

    // Setting pak name for later saving
    umgebung_t::objfilename = PAK_PATH;

    dbg->important("Reading language files ...");
    if(  !translator::load(umgebung_t::objfilename)  ) {
        dbg->error("simmain::main()", "Unable to load any language files");
    }

    // loading all paks
    dbg->important("Reading object data from %s...", PAK_PATH);
    obj_reader_t::load(PAK_PATH, "Loading paks ..." );
    dbg->debug("ReadPak", "Finished load");
    obj_reader_t::laden_abschliessen();
    dbg->debug("ReadPak", "Finished laden_abschliessen");
    pakset_info_t::calculate_checksum();
    dbg->debug("ReadPak", "Finished calculate_checksum");
    pakset_info_t::debug();
    dbg->debug("ReadPak", "Finished debug");

    dbg->important("Reading menu configuration ...");
    werkzeug_t::init_menu();

    dbg->warning( "ask_language", "No language selected, will use english!" );
    translator::set_language( "en" );

    // Define at module level some translator functions
    //
    def("set_language", set_lang_int );
    def("set_language", set_lang_chr );
    def("translate", translate_current_lang );

    def("which_work_dir", &print_work_dir );    // DEBUGGING function

    def("get_fabesch_table", get_fabesch_table,
            return_value_policy<reference_existing_object>());

    //------------------------------------
    // Export containers
    export_weighted_vector<stadt_t>("weighted_vector_stadt");
    //export_weighted_vector<stadt_t*>("weighted_vector_stadt_ptr");
    //export_weighted_vector<gebaeude_t>("weighted_vector_gebaeude");
    export_vector_tpl<koord>("vector_tpl_koord");
    export_vector_tpl<ware_besch_t const*>("vector_tpl_ware_besch_t_const_ptr");
    export_array_tpl<ware_production_t>("array_tpl_ware_production_t");

    export_stringhashtable_tpl<fabrik_besch_t const*>("stringhashtable_fabrik_besch_const_ptr");

    //------------------------------------
    // Classes definition

    char * program_dir_as_ptr = umgebung_t::program_dir; // TODO : Does not worl

    class_<umgebung_t>("umgebung_t")
        /// points to the current simutrans data directory
        .def_readonly("program_dir",
                program_dir_as_ptr )
                //&umgebung_t::program_dir )
        /// points to the current user directory for loading and saving
        .def_readonly("user_dir", &umgebung_t::user_dir )
        /// version for which the savegames should be created
        .def_readonly("savegame_version_str", &umgebung_t::savegame_version_str )
        /// name of the directory to the pak-set
        .def_readonly("objfilename", &umgebung_t::objfilename )
        .def_readwrite("verbose_debug", &umgebung_t::verbose_debug );
    ;

    class_<settings_t>("settings_t")
        .def_readonly("heightfield", &settings_t::heightfield)

        .add_property("map_size", &settings_size_as_tuple )
        .add_property("groesse_x", &settings_t::get_groesse_x )
        .add_property("groesse_y", &settings_t::get_groesse_y )
        .add_property("karte_nummer", &settings_t::get_karte_nummer )
        .add_property("factory_count", &settings_t::get_factory_count )
        .add_property("electric_promille", &settings_t::get_electric_promille )
        .add_property("tourist_attractions", &settings_t::get_tourist_attractions )
        .add_property("anzahl_staedte", &settings_t::get_anzahl_staedte )
        .add_property("mittlere_einwohnerzahl", &settings_t::get_mittlere_einwohnerzahl )
        .add_property("verkehr_level", &settings_t::get_verkehr_level )
        .add_property("show_pax", &settings_t::get_show_pax )
        .add_property("grundwasser", &settings_t::get_grundwasser )
        .add_property("max_mountain_height", &settings_t::get_max_mountain_height )
        .add_property("map_roughness", &settings_t::get_map_roughness )
        .add_property("station_coverage", &settings_t::get_station_coverage )
        .add_property("allow_player_change", &settings_t::get_allow_player_change )
        .add_property("use_timeline", &settings_t::get_use_timeline )
        .add_property("starting_year", &settings_t::get_starting_year )
        .add_property("starting_month", &settings_t::get_starting_month )
        .add_property("bits_per_month", &settings_t::get_bits_per_month )
        //const char* get_filename() const { return filename.c_str(); }
        .add_property("beginner_mode", &settings_t::get_beginner_mode )
        .add_property("just_in_time", &settings_t::get_just_in_time )
        //const sint16 *get_climate_borders() const { return climate_borders; }
        .add_property("winter_snowline", &settings_t::get_winter_snowline )
        .add_property("rotation", &settings_t::get_rotation )
        .add_property("origin_x", &settings_t::get_origin_x )
        .add_property("origin_y", &settings_t::get_origin_y )
        //bool is_freeplay() const { return freeplay; }
        .add_property("max_route_steps", &settings_t::get_max_route_steps )
        .add_property("max_hops", &settings_t::get_max_hops )
        .add_property("max_transfers", &settings_t::get_max_transfers )
        //sint64 get_starting_money(sint16 year) const;
        .add_property("special_building_distance", &settings_t::get_special_building_distance )
        .add_property("min_factory_spacing", &settings_t::get_min_factory_spacing )
        .add_property("max_factory_spacing", &settings_t::get_max_factory_spacing )
        .add_property("max_factory_spacing_percent", &settings_t::get_max_factory_spacing_percent )
        .add_property("crossconnect_factor", &settings_t::get_crossconnect_factor )
        //bool is_crossconnect_factories() const { return crossconnect_factories; }
        .add_property("numbered_stations", &settings_t::get_numbered_stations )
        .add_property("stadtauto_duration", &settings_t::get_stadtauto_duration )
        .add_property("beginner_price_factor", &settings_t::get_beginner_price_factor )
        //const weg_besch_t *get_city_road_type( uint16 year );
        //const weg_besch_t *get_intercity_road_type( uint16 year );
        .add_property("pak_diagonal_multiplier", &settings_t::get_pak_diagonal_multiplier )
        .add_property("name_language_id", &settings_t::get_name_language_id )

        //uint8 get_player_type(uint8 i) const { return spieler_type[i]; }
        //bool is_seperate_halt_capacities() const { return seperate_halt_capacities ; }

        // allowed modes are 0,1,2
        //enum { TO_PREVIOUS=0, TO_TRANSFER, TO_DESTINATION };
        //uint8 get_pay_for_total_distance_mode() const { return pay_for_total_distance ; }

        // do not take people to overcrowded destinations
        //bool is_avoid_overcrowding() const { return avoid_overcrowding; }

        // do not allow routes over overcrowded destinations
        //bool is_no_routing_over_overcrowding() const { return no_routing_over_overcrowding; }

        .add_property("river_number", &settings_t::get_river_number )
        .add_property("min_river_length", &settings_t::get_min_river_length )
        .add_property("max_river_length", &settings_t::get_max_river_length )

        // true, if this pak should be used with extensions (default)
        .add_property("with_private_paks", &settings_t::get_with_private_paks )

        .add_property("passenger_factor", &settings_t::get_passenger_factor )

        // town growth stuff
        .add_property("passenger_multiplier", &settings_t::get_passenger_multiplier )
        .add_property("mail_multiplier", &settings_t::get_mail_multiplier )
        .add_property("goods_multiplier", &settings_t::get_goods_multiplier )
        .add_property("electricity_multiplier", &settings_t::get_electricity_multiplier )

        // Also there are size dependen factors (0=no growth)
        .add_property("growthfactor_small", &settings_t::get_growthfactor_small )
        .add_property("growthfactor_medium", &settings_t::get_growthfactor_medium )
        .add_property("growthfactor_large", &settings_t::get_growthfactor_large )

        // percentage of passengers for different kinds of trips
        .add_property("factory_worker_percentage", &settings_t::get_factory_worker_percentage )
        .add_property("tourist_percentage", &settings_t::get_tourist_percentage )

        // radius from factories to get workers from towns (usually set to 77 but 1/8 of map size may be meaningful too)
        .add_property("factory_worker_radius", &settings_t::get_factory_worker_radius )

        // any factory will be connected to at least this number of next cities
        .add_property("factory_worker_minimum_towns", &settings_t::get_factory_worker_minimum_towns )

        // any factory will be connected to not more than this number of next cities
        .add_property("factory_worker_maximum_towns", &settings_t::get_factory_worker_maximum_towns )

        // Knightly : number of periods for averaging the amount of arrived pax/mail at factories
        .add_property("factory_arrival_periods", &settings_t::get_factory_arrival_periods )

        // Knightly : whether factory pax/mail demands are enforced
        .add_property("factory_enforce_demand", &settings_t::get_factory_enforce_demand )

        .add_property("factory_maximum_intransit_percentage", &settings_t::get_factory_maximum_intransit_percentage )

        //uint32 get_locality_factor(sint16 year) const;

        // disallow using obsolete vehicles in depot
        .add_property("allow_buying_obsolete_vehicles", &settings_t::get_allow_buying_obsolete_vehicles )

        // forest stuff
        //uint8 get_forest_base_size() const { return forest_base_size; }
        //uint8 get_forest_map_size_divisor() const { return forest_map_size_divisor; }
        //uint8 get_forest_count_divisor() const { return forest_count_divisor; }
        //uint16 get_forest_inverse_spare_tree_density() const { return forest_inverse_spare_tree_density; }
        //uint8 get_max_no_of_trees_on_square() const { return max_no_of_trees_on_square; }
        //uint16 get_tree_climates() const { return tree_climates; }
        //uint16 get_no_tree_climates() const { return no_tree_climates; }
        //bool get_no_trees() const { return no_trees; }

        .add_property("industry_increase_every", &settings_t::get_industry_increase_every )
        .add_property("minimum_city_distance", &settings_t::get_minimum_city_distance )

        .add_property("used_vehicle_reduction", &settings_t::get_used_vehicle_reduction )

        // usually only used in network mode => no need to set them!
        //uint32 get_random_counter() const { return random_counter; }
        //uint32 get_frames_per_second() const { return frames_per_second; }
        //uint32 get_frames_per_step() const { return frames_per_step; }
        //uint32 get_server_frames_ahead() const { return server_frames_ahead; }

        //bool is_drive_left() const { return drive_on_left; }
        //bool is_signals_left() const { return signals_on_left; }

        .add_property("way_toll_runningcost_percentage", &settings_t::get_way_toll_runningcost_percentage )
        .add_property("way_toll_waycost_percentage", &settings_t::get_way_toll_waycost_percentage )

        .add_property("bonus_basefactor", &settings_t::get_bonus_basefactor )

        .add_property("allow_underground_transformers", &settings_t::get_allow_underground_transformers )

        .add_property("remove_dummy_player_months", &settings_t::get_remove_dummy_player_months )
        .add_property("unprotect_abondoned_player_months", &settings_t::get_unprotect_abondoned_player_months )
    ;

    class_<karte_t, boost::noncopyable>("World", init<>())
        .def("load", load_fname)
        .def("save", save_welt)
        // pause methods
        .def("is_paused", &karte_t::is_paused)
        .def("set_pause", &karte_t::set_pause)

        .def("get_world_position", &karte_t::get_world_position)
        // properties
        .add_property("current_month", &karte_t::get_current_month )
        .add_property("last_month", &karte_t::get_last_month )
        .add_property("last_year", &karte_t::get_last_year )

        // @return 0=winter, 1=spring, 2=summer, 3=autumn
        .add_property("season", &karte_t::get_season )

        .add_property("ticks", &karte_t::get_zeit_ms )

        // Ideally would like to make this a read-only settings propertiy
        // but dont know how to specify the return_value_policy
        .def("get_settings", karte_get_settings,
                //return_value_policy<manage_new_object>()
                return_value_policy<copy_non_const_reference>()
            )

        .def("get_staedte", &karte_t::get_staedte,
                return_value_policy<reference_existing_object>() )
                //return_value_policy<copy_const_reference>() )

        .def("get_goods_list", &karte_t::get_goods_list,
                return_value_policy<reference_existing_object>())

        // FIXME Expose as a factoy(s) property
        .def("get_factory_count", &karte_factory_count )
        .def("get_factory_at", &karte_t::get_fab,
                return_value_policy<reference_existing_object>() )

        // Handy function
        .def("get_fab_at_kood", &fabrik_t::get_fab,
                return_value_policy<reference_existing_object>() )

        // TODO : welt->lookup(pos);
    // For mini-map generation
        .def("lookup_kartenboden", &karte_t::lookup_kartenboden,
                return_value_policy<reference_existing_object>() )
    ;

    class_<stadt_t, boost::noncopyable>("stadt_t", no_init)
        .add_property("einwohner", &stadt_t::get_einwohner )

        .add_property("buildings", &stadt_t::get_buildings )
        .add_property("unemployed", &stadt_t::get_unemployed )
        .add_property("homeless", &stadt_t::get_homeless )

        .add_property("name", &stadt_t::get_name, &stadt_t::set_name )

        .add_property("zufallspunkt", &stadt_t::get_zufallspunkt )
        .add_property("pos", &stadt_t::get_pos )
        .add_property("townhall_road", &stadt_t::get_townhall_road )
        .add_property("linksoben", &stadt_t::get_linksoben )
        .add_property("rechtsunten", &stadt_t::get_rechtsunten )
        .add_property("center", &stadt_t::get_center )
    ;

    class_<fabrik_t, boost::noncopyable>("fabrik_t", no_init)
        .add_property("besch",
                make_function( &fabrik_t::get_besch,
                return_value_policy<reference_existing_object>()
                ))

        .add_property("pos", &fabrik_t::get_pos )

        //const vector_tpl<koord>& get_lieferziele() const { return lieferziele; }
        .def("get_consumers", &fabrik_t::get_lieferziele,
            return_value_policy<reference_existing_object>())

        .def("is_active_lieferziel", &fabrik_t::is_active_lieferziel )

        //const vector_tpl<koord>& get_suppliers() const { return suppliers; }
        .def("get_suppliers", &fabrik_t::get_suppliers,
            return_value_policy<reference_existing_object>())


        //const vector_tpl<stadt_t *>& get_target_cities() const { return target_cities; }

        //array_tpl<ware_production_t>& get_eingang() const { return eingang; }
        .def("get_eingang", &fabrik_t::get_eingang,
            return_value_policy<reference_existing_object>())
        //array_tpl<ware_production_t>& get_ausgang() const { return ausgang; }
        .def("get_ausgang", &fabrik_t::get_ausgang,
            return_value_policy<reference_existing_object>())

        .add_property("is_currently_producing", &fabrik_t::is_currently_producing )
        .add_property("is_transformer_connected", &fabrik_t::is_transformer_connected )

        .add_property("name", &fabrik_t::get_name )
            // is required ?? void set_name( const char *name );

        .add_property("kennfarbe", &fabrik_t::get_kennfarbe )

        .add_property("base_production", &fabrik_t::get_base_production )
        .add_property("current_production", &fabrik_t::get_current_production )

        .add_property("status", &fabrik_t::get_status )
        .add_property("total_in", &fabrik_t::get_total_in )
        .add_property("total_transit", &fabrik_t::get_total_transit )
        .add_property("total_out", &fabrik_t::get_total_out )

        .add_property("is_end_consumer", &fabrik_t::is_end_consumer )

        // infostring on production
        //void info_prod(cbuffer_t& buf) const;
        .def("get_info_prod", &fabrik_t::info_prod) //TODO Make a property

        // infostring on targets/sources
        //void info_conn(cbuffer_t& buf) const;
        .def("get_info_conn", &fabrik_t::info_conn) //TODO Make a property
    ;

    // Replaced as an attempt to fix error
    //   No to_python (by-value) converter found for C++ type: ware_production_t
    //class_<ware_production_t, boost::noncopyable>("ware_production_t", no_init)
    class_<ware_production_t>("ware_production_t", no_init)
        .def("get_typ", &ware_production_t::get_typ,
            return_value_policy<reference_existing_object>())

        // Following methods should be shifted precision_bits, before returning
        // As a getter??
        .def_readonly("menge", &ware_production_t::menge )
        .def_readonly("max", &ware_production_t::max )
        .def_readonly("transit", &ware_production_t::transit )

        .def_readonly("index_offset", &ware_production_t::index_offset )

        .def_readonly("fabrik_precision_bits", fabrik_t::precision_bits ) // TODO: Broken
    ;

    class_<obj_besch_std_name_t>("obj_besch_std_name_t", no_init)
        .add_property("name", &obj_besch_std_name_t::get_name)
        .add_property("copyright", &obj_besch_std_name_t::get_copyright)
    ;

    class_<ware_besch_t, bases<obj_besch_std_name_t> >("ware_besch_t", no_init)

        .add_property("mass", &ware_besch_t::get_mass )
        .add_property("preis", &ware_besch_t::get_preis )

        // @return speed bonus value of the good
        .add_property("speed_bonus", &ware_besch_t::get_speed_bonus )

        // @return Category of the good
        .add_property("catg", &ware_besch_t::get_catg )

        // @return Category of the good
        .add_property("catg_index", &ware_besch_t::get_catg_index )

        // @return internal index (just a number, passenger, then mail, then something ... )
        .add_property("index", &ware_besch_t::get_index )

        // @return weight in KG per unit of the good
        .add_property("weight_per_unit", &ware_besch_t::get_weight_per_unit )

        // @return Name of the category of the good
        .add_property("catg_name", &ware_besch_t::get_catg_name )

        //bool is_interchangeable(const ware_besch_t *other) const

        .add_property("color", &ware_besch_t::get_color )

        .def("__hash__", &ware_besch_t::get_index )
        .def( self == other<ware_besch_t>() )
    ;

    class_<fabrik_produkt_besch_t>("fabrik_produkt_besch_t", no_init)
        .add_property("ware_besch",
            make_function( &fabrik_produkt_besch_t::get_ware,
            return_value_policy<reference_existing_object>()))
        .add_property("kapazitaet", &fabrik_produkt_besch_t::get_kapazitaet )
        .add_property("faktor", &fabrik_produkt_besch_t::get_faktor )
    ;

    class_<fabrik_lieferant_besch_t>("fabrik_lieferant_besch_t", no_init)
        .add_property("ware_besch",
            make_function( &fabrik_lieferant_besch_t::get_ware,
            return_value_policy<reference_existing_object>()))
        .add_property("kapazitaet", &fabrik_lieferant_besch_t::get_kapazitaet )
        .add_property("anzahl", &fabrik_lieferant_besch_t::get_anzahl )
        .add_property("verbrauch", &fabrik_lieferant_besch_t::get_verbrauch )
    ;

    using namespace boost::python;
    {
        scope in_Fabrik_besch_t = class_<fabrik_besch_t>("fabrik_besch_t", no_init)
            .add_property("name", &fabrik_besch_t::get_name )
            .add_property("copyright", &fabrik_besch_t::get_copyright )
            .add_property("haus", make_function(&fabrik_besch_t::get_haus,
                    return_value_policy<reference_existing_object>()))
            .add_property("rauch", make_function(&fabrik_besch_t::get_rauch,
                    return_value_policy<reference_existing_object>()))

            .def("get_lieferant", &fabrik_besch_t::get_lieferant,
                    return_value_policy<reference_existing_object>())
            .def("get_produkt", &fabrik_besch_t::get_produkt,
                    return_value_policy<reference_existing_object>())
            .add_property("field_group",
                    make_function(&fabrik_besch_t::get_field_group,
                    return_value_policy<reference_existing_object>()))

            .add_property("is_consumer_only", &fabrik_besch_t::is_consumer_only )
            .add_property("is_producer_only", &fabrik_besch_t::is_producer_only )

            .add_property("lieferanten", &fabrik_besch_t::get_lieferanten )
            .add_property("produkte", &fabrik_besch_t::get_produkte )

            /* where to built */
            .add_property("platzierung", &fabrik_besch_t::get_platzierung )
            .add_property("gewichtung", &fabrik_besch_t::get_gewichtung )

            .add_property("kennfarbe", &fabrik_besch_t::get_kennfarbe )

            .add_property("produktivitaet", &fabrik_besch_t::get_produktivitaet )
            .add_property("bereich", &fabrik_besch_t::get_bereich )

            /* level for post and passenger generation */
            .add_property("pax_level", &fabrik_besch_t::get_pax_level )

            .add_property("is_electricity_producer", &fabrik_besch_t::is_electricity_producer )

            .add_property("expand_probability", &fabrik_besch_t::get_expand_probability )
            .add_property("expand_minumum", &fabrik_besch_t::get_expand_minumum )
            .add_property("expand_range", &fabrik_besch_t::get_expand_range )
            .add_property("expand_times", &fabrik_besch_t::get_expand_times )

            .add_property("electric_boost", &fabrik_besch_t::get_electric_boost )
            .add_property("pax_boost", &fabrik_besch_t::get_pax_boost )
            .add_property("mail_boost", &fabrik_besch_t::get_mail_boost )
            .add_property("electric_amount", &fabrik_besch_t::get_electric_amount )
            .add_property("pax_demand", &fabrik_besch_t::get_pax_demand )
            .add_property("mail_demand", &fabrik_besch_t::get_mail_demand )
        ;

        // TODO: This gets exposed as simworld.fabrik_besch_t.site_t BUT
        // WHY does it do:
        // In [10]: simworld.fabrik_besch_t.site_t.names['Land'].__class__
        // Out[10]: <class 'simworld.site_t'>
        // In [14]: print '%r' % simworld.fabrik_besch_t.site_t.Land
        // simworld.site_t.Land
        enum_<fabrik_besch_t::site_t>("site_t")
            .value("Land", fabrik_besch_t::Land )
            .value("Wasser", fabrik_besch_t::Wasser )
            .value("Stadt", fabrik_besch_t::Stadt )
        ;

    }   // End of fabrik_besch_t scope

    class_<gebaeude_t, boost::noncopyable>("gebaeude_t", no_init)
        // Not currently needed but existent
    ;

    class_<cbuffer_t>("cbuffer_t", init<>())
        .def("get_str", &cbuffer_t::get_str )
        .def("__str__", &cbuffer_t::get_str )
        .def("__len__", &cbuffer_t::len )
    ;

    using namespace boost::python;
    {
        scope in_Grund_t = class_<grund_t, boost::noncopyable>("grund_t", no_init)
            .add_property("typ", &grund_t::get_typ )
            .add_property("is_wasser", &grund_t::ist_wasser )
            .add_property("is_halt", &grund_t::is_halt )
            .add_property("hoehe", &grund_t::get_hoehe )
            .add_property("hat_wege", &grund_t::hat_wege )
        ;

        enum_<grund_t::typ>("grund_typ")
            .value("boden", grund_t::boden )
            .value("wasser", grund_t::wasser )
            .value("fundament", grund_t::fundament )
            .value("tunnelboden", grund_t::tunnelboden )
            .value("brueckenboden", grund_t::brueckenboden )
            .value("monorailboden", grund_t::monorailboden )
        ;

    }   // End of grund_t scope

    class_<koord>("koord", init<short, short>())
        // static methods
        .def("koord_distance", koord_distance_koord_koord)
        .staticmethod("koord_distance")
        .def("shortest_distance", &shortest_distance)
        .staticmethod("shortest_distance")
        // Attributes
        .def("coords", &koord_as_tuple)
        .def("get_str", &koord::get_str )
        .def("get_fullstr", &koord::get_fullstr )
        .def_readwrite("x", &koord::x)
        .def_readwrite("y", &koord::y)
        // Operators
        .def( self == other<koord>() )
        .def( self != other<koord>() )
        .def( self_ns::str(self_ns::self) )
        .def( self_ns::repr(self_ns::self) )
    ;

    class_<koord3d>("koord3d", init<sint16, sint16, sint8>())
        // Attributes
        //.def("coords", &koord_as_tuple)
        .def("get_str", &koord3d::get_str )
        .def("get_fullstr", &koord3d::get_fullstr )
        .def("get_2d", &koord3d::get_2d )
        .def_readonly("x", &koord3d::x)
        .def_readonly("y", &koord3d::y)
        .def_readonly("z", &koord3d::z)
        // Operators
        .def( self == other<koord3d>() )
        .def( self != other<koord3d>() )
        .def( self_ns::str(self_ns::self) )
        .def( self_ns::repr(self_ns::self) )
    ;

}
